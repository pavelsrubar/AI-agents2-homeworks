import json
import sys
import asyncio
from mcp.server.lowlevel import Server
import mcp.types as types
from mcp.server.stdio import stdio_server

from tools.generate_random_multiplied import generate_random_multiplied
from tools.generate_random_divided import generate_random_divided

server = Server("mcp-randoms")

async def run_server():
    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        print("\nMCP Server - LIST TOOLS invoked from client", file=sys.stderr, flush=True)
        return [
            types.Tool(
                name="generate_random_multiplied",
                description="Use this function to get random number in given range, miltiplied by given number.",
                inputSchema={
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
            ),
            types.Tool(
                name="generate_random_divided",
                description="Use this function to get random number in given range, divided by given number.",
                inputSchema={
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
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        print("\nMCP Server - CALL TOOL invoked from client", file=sys.stderr, flush=True)
        print(name, file=sys.stderr, flush=True)
        print(arguments, file=sys.stderr, flush=True)

        result = None
        if name == "generate_random_multiplied":
            result = generate_random_multiplied(arguments["minimum"], arguments["maximum"], arguments["multiplier"])
        elif name == "generate_random_divided":
            result = generate_random_divided(arguments["minimum"], arguments["maximum"], arguments["divisor"])

        print("Result:", file=sys.stderr, flush=True)
        print(result, file=sys.stderr, flush=True)

        result_json = json.dumps(result)

        return [types.TextContent(type="text", text=result_json)]

    # run the server
    print("Starting MCP server...", file=sys.stderr, flush=True)
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(run_server())
