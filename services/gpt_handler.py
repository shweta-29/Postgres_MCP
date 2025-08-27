"""
gpt_handler.py - This is MCP client that connects to MCP server and lets GPT know about the tool

This script sends the user's text query to GPT.
But instead of GPT returning raw MongoDB queries,
it can only call our MCP tool (run_mongo_query_tool) defined in mcp_server.py.

So GPT:
  1. Reads the user query in natural language.
  2. Decides which tool to call.
  3. Calls our Mongo tool with structured JSON (collection, filter, limit).
  4. We run that Mongo query and return results.
"""

import os
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client # Helper that launches an MCP server as a subprocess and connects over stdin/stdout pipes.Basically: stdio_client("python services/mcp_server.py") runs the MCP server and gives you streams to talk to it.
from mcp.client import Client # Client wraps those streams into a proper MCP client object.With it, you can: list_tools() → see what tools the server exposes, call_tool() → actually call the tool
# OpenAI client setup (needs your API key in environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def generate_mongo_query(user_query: str):
    """
    Main function called by app.py
    Takes the user's natural language query -> sends to GPT -> gets results from MCP Mongo tool.
    """

    # ---- 1. Start MCP client ----
    # This connects to the MCP server (mcp_server.py) that exposes Mongo tool.
    async with stdio_client("python services/mcp_server.py") as streams:
        mcp_client = Client(*streams)

        # Create a session for tool calls
        async with mcp_client.session() as session:

            # ---- 2. Ask server which tools are available ----
            tools = await session.list_tools()
            # (It should list: run_mongo_query_tool)

            # ---- 3. Send user query to GPT ----
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",  # cheap + good for MVP
                messages=[
                    {"role": "system", "content": "Use the Mongo tool to answer user queries."},
                    {"role": "user", "content": user_query},
                ],
                tools=tools,        # Tell GPT what tools it can use
                tool_choice="auto"  # Let GPT decide when to call the tool
            )

            # ---- 4. Check if GPT called our tool ----
            msg = resp.choices[0].message
            if msg.tool_calls:
                # First tool call
                call = msg.tool_calls[0]

                # ---- 5. Execute the tool call on our MCP server ----
                tool_resp = await session.call_tool(call)

                # ---- 6. Return the results back to app.py ----
                return {
                    "mongo_query": call.function.arguments,  # what GPT asked for
                    "results": tool_resp["results"],         # actual Mongo results
                    "meta": {"model": "gpt-4o-mini", "via_mcp": True}
                }
            else:
                raise ValueError("GPT did not call the Mongo tool")
