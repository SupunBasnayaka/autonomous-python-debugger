
import subprocess
import sys
import tempfile
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


# Load environment variables
load_dotenv()

# Initialize the language model
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# Ask the LLM to fix Python code
def fix_code(code, error):
    prompt = f"""
You are an expert Python debugging assistant.

Fix the Python code using the error message.

Rules:
1. Return only corrected Python code.
2. Do not use Markdown code fences.
3. Preserve the original purpose of the code.
4. Fix the underlying problem.
5. Do not add unnecessary explanations.

Original Python code:
{code}

Error message:
{error}
"""

    response = llm.invoke(prompt)
    return response.content.strip()


# Execute Python code and capture its output or error
def run_code(code):
    file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False
        ) as file:
            file.write(code)
            file_path = file.name

        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Execution timed out after 5 seconds."
        }

    except OSError as e:
        return {
            "success": False,
            "output": "",
            "error": f"Execution error: {e}"
        }

    finally:
        if file_path is not None:
            try:
                os.remove(file_path)
            except OSError:
                pass


# Agent loop: execute, observe, fix, and retry
def agent_loop(code, max_attempts=5):
    current_code = code

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")

        # Execute the current code
        result = run_code(current_code)

        # Stop if execution succeeds
        if result["success"]:
            print("Code executed successfully!")
            print("Output:")
            print(result["output"])

            return {
                "success": True,
                "code": current_code,
                "output": result["output"],
                "error": ""
            }

        # Display the error
        print("Execution failed.")
        print("Error:")
        print(result["error"])

        # Stop if the attempt limit is reached
        if attempt == max_attempts:
            print("Maximum attempts reached.")

            return {
                "success": False,
                "code": current_code,
                "output": result["output"],
                "error": result["error"]
            }

        # Ask the LLM to fix the latest code
        print("Asking the LLM to fix the code...")

        try:
            current_code = fix_code(
                current_code,
                result["error"]
            )
        except Exception as e:
            print(f"LLM request failed: {e}")

            return {
                "success": False,
                "code": current_code,
                "output": result["output"],
                "error": f"LLM request failed: {e}"
            }

    return {
        "success": False,
        "code": current_code,
        "output": "",
        "error": "Agent stopped without a successful execution."
    }


# Main program
if __name__ == "__main__":

    code = """
numbers = [10, 20, 30, 40, 50]
average = sum(numbers) / len(number)
print("Average:", average)
"""

    result = agent_loop(code, max_attempts=5)

    print("\n========== FINAL RESULT ==========")
    print("Success:", result["success"])

    print("\nFinal code:")
    print(result["code"])

    if result["success"]:
        print("\nFinal output:")
        print(result["output"])
    else:
        print("\nFinal error:")
        print(result["error"])
