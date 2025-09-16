from fastapi import APIRouter, HTTPException
import vertexai
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel
from models import ChatRequest, ChatResponse
import numpy as np
import scann
import os

router = APIRouter()

# --- Configuration ---
GCP_PROJECT = os.getenv("GCP_PROJECT", "h2s-hack")
GCP_REGION = "europe-west1"
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

# --- THE FIX IS ON THIS LINE ---
# Using the most stable and widely available model version
embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
chat_model = GenerativeModel("gemini-1.0-pro")
# ---

def chunk_text(text, chunk_size=500, chunk_overlap=100):
    if not text: return []
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - chunk_overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

@router.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    if not request.sanitized_text or not request.question:
        raise HTTPException(status_code=400, detail="Text and question cannot be empty.")
    try:
        text_chunks = chunk_text(request.sanitized_text)
        if not text_chunks:
            return ChatResponse(answer="The document appears to be empty or too short to analyze.")
        
        doc_embeddings = embedding_model.get_embeddings(text_chunks)
        question_embedding = embedding_model.get_embeddings([request.question])
        
        doc_vectors = np.array([e.values for e in doc_embeddings])
        question_vector = np.array(question_embedding[0].values)

        searcher = scann.scann_ops_pybind.builder(doc_vectors, 10, "dot_product").tree(
            num_leaves=int(np.sqrt(len(doc_vectors))), num_leaves_to_search=10, training_sample_size=256
        ).score_ah(2, anisotropic_quantization_threshold=0.2).reorder(100).build()
        
        neighbors, _ = searcher.search(question_vector, final_num_neighbors=1)
        context = text_chunks[neighbors[0]]

        prompt = f"""
        Context:
        ---
        {context}
        ---
        Question: {request.question}
        Based only on the context provided, answer the user's question. If the context does not contain the answer, say "I could not find the answer in the document."
        """

        response = chat_model.generate_content(prompt)
        return ChatResponse(answer=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during chat processing: {e}")