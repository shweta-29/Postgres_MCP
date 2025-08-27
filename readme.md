Process Flow (end-to-end)

1. User enters query
Example: “Show me all customers from London”.
The frontend sends this text to app.py.

2. Backend receives query (app.py)

Calls generate_mongo_query(user_query) in gpt_handler.py.

3. GPT handler starts MCP client (gpt_handler.py)

Launches MCP server (mcp_server.py) as a subprocess.

Lists available tools (in our case, run_mongo_query_tool).

4. Send user query to GPT

GPT sees: “You can only use the Mongo tool to answer”.

GPT decides: I need customer data from customers collection where city = London.

GPT calls the MCP tool with parameters:

{
  "collection": "customers",
  "filter": {"city": "London"},
  "limit": 50
}


5. MCP server executes query (mcp_server.py)

Runs MongoDB find query with given parameters.

Returns the list of documents (converted to Python dicts).

6. Results flow back

MCP server → GPT handler → app.py.

Backend sends the results back to frontend as JSON.

7. Frontend displays

User sees the results in a table/JSON viewer.

👉 This way, GPT never writes raw Mongo queries itself. It only chooses tool parameters.
The MCP server is the only place that touches MongoDB, which keeps things safe and transparent.Process Flow (end-to-end)

User enters query
Example: “Show me all customers from London”.
The frontend sends this text to app.py.

Backend receives query (app.py)

Calls generate_mongo_query(user_query) in gpt_handler.py.

GPT handler starts MCP client (gpt_handler.py)

Launches MCP server (mcp_server.py) as a subprocess.

Lists available tools (in our case, run_mongo_query_tool).

Send user query to GPT

GPT sees: “You can only use the Mongo tool to answer”.

GPT decides: I need customer data from customers collection where city = London.

GPT calls the MCP tool with parameters:

{
  "collection": "customers",
  "filter": {"city": "London"},
  "limit": 50
}


MCP server executes query (mcp_server.py)

Runs MongoDB find query with given parameters.

Returns the list of documents (converted to Python dicts).

Results flow back

MCP server → GPT handler → app.py.

Backend sends the results back to frontend as JSON.

Frontend displays

User sees the results in a table/JSON viewer.

👉 This way, GPT never writes raw Mongo queries itself. It only chooses tool parameters.
The MCP server is the only place that touches MongoDB, which keeps things safe and transparent.