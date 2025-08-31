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

import config
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client # Helper that launches an MCP server as a subprocess and connects over stdin/stdout pipes.Basically: stdio_client("python services/mcp_server.py") runs the MCP server and gives you streams to talk to it.
from mcp import ClientSession, StdioServerParameters # Client wraps those streams into a proper MCP client object.With it, you can: list_tools() → see what tools the server exposes, call_tool() → actually call the tool
import httpx
import json
from pydantic import BaseModel
from typing import List

# OpenAI client setup (needs your API key in environment)
client = AsyncOpenAI(
    api_key=config.OPENAI_API_KEY,
    http_client=httpx.AsyncClient(verify=False)  # DEV ONLY
)

def get_prompt_to_identify_tool_and_arguments(query,tools):
    tools_description = "\n".join([f"- {tool.name}, {tool.description}, {tool.inputSchema} " for tool in tools])
    return  ("You are a helpful assistant with access to these tools:\n\n"
                f"{tools_description}\n"
                "Choose the appropriate tool based on the user's question. \n"
                f"User's Question: {query}\n"                
                "If no tool is needed, reply directly.\n\n"
                "IMPORTANT: When you need to use a tool, you must ONLY respond with "                
                "the exact JSON object format below, nothing else:\n"
                "Keep the values in str "
                "{\n"
                '    "tool": "tool-name",\n'
                '    "arguments": {\n'
                '        "argument-name": "value"\n'
                "    }\n"
                "}\n\n")

SYSTEM_PROMPT = (
  "Translate the user's request into JSON arguments for 'run_mongo_query_tool'. "
  "Output ONLY a JSON object with keys: collection (string), filter (object), "
  "projection (object or null), sort (array of [field, direction] or null), limit (integer)."
)

# Define server parameters to run the server
server_params = StdioServerParameters(
    command="python",              # The executable to run
    args=["services/mcp_server.py"], # The server script 
    env=None                       # Optional: environment variables (None uses defaults)
)

# Function to generate JSON schema from a Pydantic model and apply 'additionalProperties': False without duplicates
def pydantic_model_to_json_schema(model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    return add_no_additional_properties(schema)


# Function to recursively add 'additionalProperties': False to all object definitions
def add_no_additional_properties(schema: dict) -> dict:
    """Recursively adds 'additionalProperties': False to all objects once without duplication."""
    if isinstance(schema, dict):
        if schema.get("type") == "object" and "additionalProperties" not in schema:
            schema["additionalProperties"] = False
        for key, value in schema.items():
            if isinstance(value, dict):
                add_no_additional_properties(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        add_no_additional_properties(item)
    return schema

class params(BaseModel):
    collection: str         # which collection/table to query
    filter: str       # conditions, e.g. {"city": "London"}
    projection: str  # choose which fields to return, e.g. {"name": 1, "email": 1}
    sort: List[str]       # order results, e.g. [["createdAt", -1]]
    limit: int   

class schema(BaseModel):
    params: params
# schema = pydantic_model_to_json_schema(MongoQueryParams)

# print('schema')
# print(schema)


async def generate_mongo_query(user_query: str):

    # 1) Start MCP server and call tool
    async with stdio_client(server_params) as (r, w):
        # Create a client session to communicate with the server
        async with ClientSession(r, w) as session:
            # Initialize the connection to the server
            await session.initialize()
            # ---- 2. Ask server which tools are available ----
            tools = await session.list_tools()

            # (It should list: run_mongo_query_tool)
            # SYSTEM_PROMPT = get_prompt_to_identify_tool_and_arguments(user_query,tools.tools)

        # 2) Get args from GPT
            resp = await client.chat.completions.parse(
                model="gpt-4o-mini",  # cheap + good for MVP
                messages=[
                    {"role": "system", "content": "Provide paramters for MongoDB"}, 
                    {"role": "user", "content": user_query},
                ],
                response_format=schema,
                max_tokens=100
            )
            raw = resp.choices[0].message.content
            print(type(raw))
            args = json.loads(raw) 

            result = await session.call_tool("run_mongo_query_tool", arguments=args)

    return {"mongo_query": args, "results": result.get("results", result)}
