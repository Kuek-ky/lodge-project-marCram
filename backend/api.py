from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from io import StringIO
from dotenv import load_dotenv
from pydantic import BaseModel

from ai_model import marcram_chat
import uvicorn
import os
import re

app = FastAPI(title="MarCraM Chatbot API")

API_BASE_URL = os.getenv("API_BASE_URL");
API_BASE_PORT = os.getenv("API_BASE_PORT");

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Chatbot API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message and get a response from the MarCraM chatbot"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = marcram_chat(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, port=int(API_BASE_PORT), host="0.0.0.0",)