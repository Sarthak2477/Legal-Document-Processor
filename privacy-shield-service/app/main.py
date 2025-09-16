from fastapi import FastAPI
from routers import redact

app = FastAPI(
    title="Legal Document Analysis API",
    description="An API for redacting PII and answering questions about legal documents.",
    version="1.0.0"
)

# Include the routers from the other files
app.include_router(redact.router, tags=["PII Redaction"])


@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok"}