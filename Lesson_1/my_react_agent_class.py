import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


# Function Implementations
def generate_random_multiplied(minimum: str, maximum: str, multiplier: str) -> dict:
    """Generates a random number in range and multiplies it."""
    multiplier_int = int(multiplier)
    random_num = random.randint(int(minimum), int(maximum))
    result = random_num * multiplier_int
    
    return {
        "random_number": random_num,
        "multiplier": multiplier,
        "result": result
    }

def generate_random_divided(minimum: str, maximum: str, divisor: str) -> dict:
    """Generates a random number in range and divides it."""
    divisor_int = int(divisor)
    random_num = random.randint(int(minimum), int(maximum))
    result = random_num / divisor_int
    
    return {
        "random_number": random_num,
        "divisor": divisor,
        "result": result
    }


# Define custom tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_random_multiplied",
            "description": "Use this function to get random number in given range, miltiplied by given number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minimum": {
                        "type": "string",
                        "description": "Minimum range value for random number generation",
                    },
                    "maximum": {
                        "type": "string",
                        "description": "Maximum range value for random number generation",
                    },
                    "multiplier": {
                        "type": "string",
                        "description": "Multiplier for the resulting return value ",
                    },
                },
                "required": ["minimum", "maximum", "multiplier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_random_divided",
            "description": "Use this function to get random number in given range, divided by given number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minimum": {
                        "type": "string",
                        "description": "Minimum range value for random number generation",
                    },
                    "maximum": {
                        "type": "string",
                        "description": "Maximum range value for random number generation",
                    },
                    "divisor": {
                        "type": "string",
                        "description": "Divisor for the resulting return value ",
                    },
                },
                "required": ["minimum", "maximum", "divisor"],
            },
        },
    },
]

available_functions = {
    "generate_random_multiplied": generate_random_multiplied,
    "generate_random_divided": generate_random_divided
}


class ReactAgent:
    def __init__(self, model: str = "gpt-5"):
        self.model = model
        self.max_iterations = 10  # Prevent infinite loops

    def run(self, messages: List[Dict[str, Any]]) -> str:
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Call the LLM
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False,
            )

            response_message = response.choices[0].message
            print(f"LLM Response: {response_message}")

            # Check if there are tool calls
            if response_message.tool_calls:
                # Add the assistant's message with tool calls to history
                messages.append(
                    {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in response_message.tool_calls
                        ],
                    }
                )

                # Process ALL tool calls (not just the first one)
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    tool_id = tool_call.id

                    print(f"\nExecuting tool: {function_name}({function_args})")

                    # Call the function
                    function_to_call = available_functions[function_name]
                    function_response = function_to_call(**function_args)

                    print(f"\nTool result: {function_response}")

                    # Add tool response to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    )

                # Continue the loop to get the next response
                continue

            else:
                # No tool calls - we have our final answer
                final_content = response_message.content

                # Add the final assistant message to history
                messages.append({"role": "assistant", "content": final_content})

                print(f"\nFinal answer: {final_content}")
                return final_content

        # If we hit max iterations, return an error
        return "Error: Maximum iterations reached without getting a final answer."


def main():
    # Create a ReAct agent
    agent = ReactAgent()

    print("=== Single Tool 1 Call ===")
    messages1 = [
        {"role": "system", "content": "You are a helpful AI assistant. "},
        {"role": "user", "content": "Give me a random number from range 1 to 10, multiplied by 6. Include random numer in answer"},
    ]

    result1 = agent.run(messages1.copy())
    print(f"\nResult: {result1}\n")

    print("=== Single Tool 2 Call ===")
    messages2 = [
        {"role": "system", "content": "You are a helpful AI assistant. "},
        {"role": "user", "content": "Give me a random number from range 65 to 81, divided by 3. Include random numer in answer"},
    ]

    result2 = agent.run(messages2.copy())
    print(f"\nResult: {result2}\n")

    print("=== Simple call without tool, using direct LLM answer ===")
    messages3 = [
        {"role": "system", "content": "You are a helpful AI assistant. "},
        {"role": "user", "content": "Give me a result of 5 plus 6"},
    ]

    result3 = agent.run(messages3.copy())
    print(f"\nResult: {result3}\n")


if __name__ == "__main__":
    main()
