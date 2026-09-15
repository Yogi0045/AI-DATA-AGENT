import psycopg2


class DatabaseUtil:

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None

        try:
            self.connection = psycopg2.connect(**db_config)
            print("Database connected successfully.")

        except Exception as e:
            print(f"Error connecting to the database: {e}")


    def schema_details(self, schema_name):

        schema_info_context = f"Database Schema: {schema_name}\n"

        connection = self.connection
        cursor = None

        try:
            cursor = connection.cursor()

            # Get all tables
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE';
                """,
                (schema_name,)
            )

            tables_list = cursor.fetchall()

            # Process each table
            for table in tables_list:

                table_name = table[0]

                schema_info_context += f"\nTable: {table_name}\n"

                # Get columns for this table
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (schema_name, table_name)
                )

                columns_list = cursor.fetchall()

                # Add columns
                for column in columns_list:

                    column_name = column[0]
                    data_type = column[1]

                    schema_info_context += (
                        f"  Column: {column_name}, "
                        f"Data Type: {data_type}\n"
                    )

                # Get sample data
                cursor.execute(
                    f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 5;'
                )

                sample_data = cursor.fetchall()

                schema_info_context += "  Sample Data:\n"

                for row in sample_data:
                    schema_info_context += f"    {row}\n"

        except Exception as e:

            print(f"Error retrieving schema details: {e}")

            schema_info_context = (
                f"Error retrieving schema details: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

        return schema_info_context


    def execute_sql(self, query):

        connection = None
        cursor = None

        try:

            # Create a new connection
            connection = psycopg2.connect(**self.db_config)

            cursor = connection.cursor()

            cursor.execute(query)

            result = cursor.fetchall()

            connection.commit()

            return str(result)

        except Exception as e:

            print(f"Error executing query: {e}")

            # Return error as string instead of None
            return f"Error executing query: {e}"

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

obj = DatabaseUtil({
    "host": "localhost",
    "port": 5432,
    "user": "yogendraadiyarapu",
    "password": "Eshwarrao@2244",
    "database": "postgres"
})

result = obj.schema_details("public")

with open("new_schema_details.txt", "w") as f:
    f.write(result)