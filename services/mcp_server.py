"""
mcp_server.py

This script creates an MCP server that exposes ONE tool:
  run_mongo_query_tool()

The tool lets GPT safely ask MongoDB for data.
Instead of GPT writing raw queries itself, it calls this tool with
structured parameters. This keeps things safe and predictable.
"""

# Import MCP FastAPI helper and MongoDB client
from mcp.server.fastapi import FastAPI, serve
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

# ---- 1. Connect to MongoDB ----
# This connects to MongoDB running locally on default port.
# "testdb" will be our database name.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "testdb"

client = AsyncIOMotorClient(MONGO_URI)  # async MongoDB client
db = client[DB_NAME]                    # select database


# ---- 2. Define tool input schema ----
# This tells GPT exactly what arguments are allowed.
# Example call: { "collection": "customers", "filter": {"city": "London"}, "limit": 10 }
class MongoQueryParams(BaseModel):
    collection: str         # which collection/table to query
    filter: dict = {}       # conditions, e.g. {"city": "London"}
    projection: dict = None # choose which fields to return, e.g. {"name": 1, "email": 1}
    sort: list = None       # order results, e.g. [["createdAt", -1]]
    limit: int = 50         # maximum number of rows


# ---- 3. Create MCP server ----
mcp = FastAPI()

# ---- 4. Define tool that Mongo queries will run through ----
@mcp.tool()
async def run_mongo_query_tool(params: MongoQueryParams):
    """
    Runs a MongoDB query with the given parameters.
    GPT will call this function instead of writing raw queries.
    """

    # pick the collection (like choosing a table in SQL)
    coll = db[params.collection]

    # build a query cursor
    cursor = coll.find(params.filter, params.projection)

    # apply sorting if given
    if params.sort:
        cursor = cursor.sort(params.sort)

    # apply limit
    cursor = cursor.limit(params.limit)

    # fetch results into a Python list
    results = [dict(doc) async for doc in cursor]

    # return results to GPT/backend
    return {"results": results}


# ---- 5. Run the MCP server if script is executed directly ----
if __name__ == "__main__":
    import asyncio
    # "mongo-server" is just the name of this MCP server
    asyncio.run(serve("mongo-server", mcp)) #serve starts the MCP server process and publishes the registered tools so an MCP client can list and call them.
