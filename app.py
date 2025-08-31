from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.gpt_handler import generate_mongo_query

app = FastAPI(title="MCP Query API")

# Allow your frontend origin(s). For quick dev, "*" is fine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],          # includes OPTIONS
    allow_headers=["*"],
)

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

#run this using: uvicorn app:app --reload
