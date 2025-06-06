from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    sender_phone: str
    receiver_phone: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ChatInteraction(BaseModel):
    chat_request: ChatRequest
    chat_response: ChatResponse
    timestamp: datetime
    language: str 