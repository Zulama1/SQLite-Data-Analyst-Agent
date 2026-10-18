import os 
import json
import sqlite3
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

DB_PATH="database.db"
client = genai.Client()

def get_schema() -> str:
    """
    Returns the SQL schema for all tables in the DB
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return "\n\n".join(t[0] for t in tables if t[0])

def run_query(query:str) -> str:
    """
    Executes a SQL query and returns rows as JSON or the exact SQLite error
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        return json.dumps({"columns":columns, "rows":rows})
    except Exception as e:
        conn.close()
        return f"Database error: {str(e)}"

TOOL_MAP={
    "get_schema": get_schema,
    "run_query":run_query,
}
def run_agent(user_prompt: str, max_steps: int = 10):
    system_instruction = (
        "You are an expert data analyst assistant with access to a SQLite database. "
        "Always inspect the database schema first if you do not know the exact column names. "
        "If a query results in an error, analyze the error and correct your query."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[get_schema, run_query],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.0,
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)],
        )
    ]

    for step in range(max_steps):
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents,
            config=config,
        )

        contents.append(response.candidates[0].content)

        if not response.function_calls:
            print("\nFinal Answer:\n", response.text)
            return

        # Handle all function calls requested by the model
        function_response_parts = []
        for call in response.function_calls:
            func_name = call.name
            args = call.args  

            print(f"[Step {step + 1}] Calling tool: {func_name}({args})")

            tool_func = TOOL_MAP.get(func_name)
            if tool_func:
                output = tool_func(**args)
            else:
                output = f"Unknown tool: {func_name}"

            function_response_parts.append(
                types.Part.from_function_response(
                    name=func_name,
                    response={"result": output},
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts,
            )
        )

    print("Reached maximum step limit without a conclusion.")

if __name__ == "__main__":
    prompt = "Who are the top 3 customers who ordered the most recently?"
    run_agent(prompt)