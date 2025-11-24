import os
import json
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

async def get_completion_from_messages(messages, session, tools, model="gpt-4o"):
    iteration = 0
    max_iterations = 10

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        # Call the LLM
        response = client.chat.completions.create(
            model=model,
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
                # Call function on MCP server
                function_response = await session.call_tool(function_name, function_args)
                print(f"\nTool result: {function_response}")

                # Add tool response to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": function_name,
                        "content": function_response.content,
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

def mcp_tools_to_openai(mcp_tools: list[types.Tool]) -> list[dict]:
    openai_tools = []
    for tool in mcp_tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema  # MCP uses JSON Schema
            }
        }
        openai_tools.append(openai_tool)
    return openai_tools

async def main():
    server_script = "../my_server/my_mcp_server.py"  # Path to the MCP server script
    server_venv_python = "../my_server/.venv/bin/python"
    server_params = StdioServerParameters(command=server_venv_python, args=[server_script])
    # establish klient connection to server and create session
    async with stdio_client(server_params) as stdio_transport:
        async with ClientSession(*stdio_transport) as mcp_session:
            result = await mcp_session.initialize()
            # Get MCP server list of available tools
            mcp_tools_response = await mcp_session.list_tools()
            mcp_tools = mcp_tools_response.tools
            print("\n=== Available Tools ===")
            for tool in mcp_tools:
                print(f"Tool name: {tool.name}, Description: {tool.description}")
            # convert MCP tools format to OpenAI format
            openai_tools = mcp_tools_to_openai(mcp_tools)

            print("\n=== Single Tool 1 Call ===")
            messages1 = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Give me a random number from range 1 to 10, multiplied by 6. Include random numer in answer"},
            ]
            result1 = await get_completion_from_messages(messages1, mcp_session, openai_tools, "gpt-5")
            print(f"\nResult: {result1}")

            print("\n=== Single Tool 2 Call ===")
            messages2 = [
                {"role": "system", "content": "You are a helpful AI assistant. "},
                {"role": "user", "content": "Give me a random number from range 65 to 81, divided by 3. Include random numer in answer"},
            ]
            result2 = await get_completion_from_messages(messages2, mcp_session, openai_tools)
            print(f"\nResult: {result2}")

            print("\n=== Simple call without tool, using direct LLM answer ===")
            messages3 = [
                {"role": "system", "content": "You are a helpful AI assistant. "},
                {"role": "user", "content": "Give me a result of 5 plus 6"},
            ]
            result3 = await get_completion_from_messages(messages3, mcp_session, openai_tools)
            print(f"\nResult: {result3}\n")

if __name__ == "__main__":
    asyncio.run(main())

