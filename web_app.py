import logging
import io
import ipaddress
import socket
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

import pandas as pd
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Agent")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=12)


class ExtractRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


def ask_sql_analyst(
    question: str, history: list[ConversationMessage] | None = None
) -> str:
    from agents.sql_analyst import sql_analyst

    recent_history = (history or [])[-6:]
    if recent_history:
        context = "\n".join(
            f"{message.role.capitalize()}: {message.content.strip()}"
            for message in recent_history
            if message.content.strip()
        )
        if context:
            question = f"Conversation so far:\n{context}\n\nCurrent question: {question}"

    result = sql_analyst.invoke(
        {
            "messages": [],
            "user_question": question,
            "curated_ques": "",
            "prompt_query_context": "",
            "generated_sql_query": "",
            "is_safe": "No",
            "comments": "",
            "sql_query_execution_result": "",
            "final_answer": "",
        }
    )
    return result["final_answer"]


@app.post("/api/chat")
def chat(payload: ChatRequest):
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a question to continue.")

    try:
        return {"answer": ask_sql_analyst(question, payload.history)}
    except Exception as exc:
        logger.exception("SQL analyst request failed")
        raise HTTPException(
            status_code=500,
            detail="The data agent could not answer that question. Please try again.",
        ) from exc


def invoke_etl_agent(instruction: str) -> str:
    from agents.etl_analyst import etl_analyst
    from langchain_core.messages import HumanMessage

    result = etl_analyst.invoke({"messages": [HumanMessage(content=instruction)]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    return str(messages[-1].content)


def dataframe_profile(frame: pd.DataFrame, filename: str) -> dict:
    columns = [
        {
            "name": str(column),
            "type": str(frame.dtypes.iloc[index]),
            "missing": int(frame.isna().sum().iloc[index]),
        }
        for index, column in enumerate(frame.columns)
    ]
    preview = frame.head(5).fillna("").astype(str).to_dict(orient="records")
    return {
        "filename": filename,
        "rows": int(len(frame)),
        "column_count": len(columns),
        "columns": columns,
        "preview": preview,
    }


def validate_public_api_url(url: str) -> None:
    try:
        parsed_url = urlsplit(url)
        port = parsed_url.port
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid HTTP or HTTPS URL.") from exc

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or port not in {None, 80, 443}
    ):
        raise HTTPException(status_code=422, detail="Enter a public HTTP or HTTPS API URL.")

    try:
        addresses = {
            ipaddress.ip_address(result[4][0])
            for result in socket.getaddrinfo(parsed_url.hostname, port or 0, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="The API hostname could not be resolved.") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise HTTPException(status_code=422, detail="API URLs must resolve to a public host.")


@app.post("/api/etl/extract")
def extract_api(payload: ExtractRequest):
    url = payload.url.strip()
    validate_public_api_url(url)

    output_folder = Path("data/extract/web_runs") / uuid4().hex
    csv_path = BASE_DIR / output_folder / "extracted_data.csv"
    instruction = (
        "Extract the JSON records from this API and save them as CSV. "
        "Use extract_load_tool exactly once with these exact arguments: "
        f"url={url!r}, output_folder={str(output_folder)!r}, format='csv'. "
        "Do not transform the data or call any other tool."
    )

    try:
        invoke_etl_agent(instruction)
        if not csv_path.is_file():
            raise HTTPException(
                status_code=502,
                detail="The ETL agent could not extract records from that URL.",
            )
        frame = pd.read_csv(csv_path)
        profile = dataframe_profile(frame, csv_path.name)
        profile["source_url"] = url
        profile["saved_to"] = str(output_folder / csv_path.name)
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("ETL API extraction failed")
        raise HTTPException(
            status_code=502,
            detail="The API response could not be extracted as CSV.",
        ) from exc


@app.post("/api/etl/upload")
async def upload_csv(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a .csv file.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV files must be 10 MB or smaller.")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded CSV is empty.")

    try:
        frame = pd.read_csv(io.BytesIO(content))
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="The file could not be read as CSV.") from exc

    upload_folder = BASE_DIR / "data" / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)
    upload_path = upload_folder / f"{uuid4().hex}.csv"
    upload_path.write_bytes(content)
    profile = dataframe_profile(frame, filename)
    profile["saved_to"] = str(upload_path.relative_to(BASE_DIR))
    return profile