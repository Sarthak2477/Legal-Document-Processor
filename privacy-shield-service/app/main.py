from fastapi import FastAPI
from routers import redact, chat

app = FastAPI(
    title="Legal Document Analysis API",
    description="An API for redacting PII and answering questions about legal documents.",
    version="1.0.0"
)

# Include the routers from the other files
app.include_router(redact.router, tags=["PII Redaction"])
app.include_router(chat.router, tags=["Document Chat (RAG)"])

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok"}