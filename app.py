from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.gpt_handler import generate_mongo_query

app = FastAPI(title="MCP Query API")

class QueryRequest(BaseModel):
    user_query: str

@app.post("/query")
async def query_data(request: QueryRequest):
    try:
        # GPT calls MCP tool internally; returns results
        output = await generate_mongo_query(request.user_query)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
