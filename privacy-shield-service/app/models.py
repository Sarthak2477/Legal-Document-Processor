from pydantic import BaseModel

class RedactionRequest(BaseModel):
    text: str

class RedactionResponse(BaseModel):
    sanitized_text: str

class ChatRequest(BaseModel):
    sanitized_text: str
    question: str

class ChatResponse(BaseModel):
    answer: str