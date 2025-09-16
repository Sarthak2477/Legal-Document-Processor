import functions_framework
import requests
import json
from google.cloud import documentai, firestore
from google.protobuf.json_format import MessageToJson # <--- ADD THIS IMPORT
import os

# --- Configuration is now read from Environment Variables ---
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION")
DOC_AI_PROCESSOR_ID = os.getenv("DOC_AI_PROCESSOR_ID")
PRIVACY_SHIELD_URL = os.getenv("PRIVACY_SHIELD_URL")

# --- Check that all required variables are set ---
REQUIRED_VARS = [GCP_PROJECT, GCP_REGION, DOC_AI_PROCESSOR_ID, PRIVACY_SHIELD_URL]
if not all(REQUIRED_VARS):
    raise RuntimeError("Missing one or more required environment variables.")

firestore_client = firestore.Client()
docai_client = documentai.DocumentProcessorServiceClient()
FIRESTORE_COLLECTION = "legal_documents"

@functions_framework.cloud_event
def trigger_extractor(cloud_event):
    data = cloud_event.data
    bucket = data["bucket"]
    filename = data["name"]

    print(f"File uploaded: {filename} in bucket: {bucket}.")
    
    document_id = filename.replace("/", "_")
    doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(document_id)
    doc_ref.set({"status": "PROCESSING", "filename": filename})

    try:
        gcs_uri = f"gs://{bucket}/{filename}"
        full_processor_name = docai_client.processor_path(GCP_PROJECT, GCP_REGION, DOC_AI_PROCESSOR_ID)
        request = documentai.ProcessRequest(
            name=full_processor_name,
            gcs_document=documentai.GcsDocument(gcs_uri=gcs_uri, mime_type="application/pdf")
        )
        result = docai_client.process_document(request=request)
        
        # --- CHANGE #1: Convert the full result to a JSON-friendly format ---
        document_ai_json = json.loads(MessageToJson(result.document._pb))
        extracted_text = result.document.text
        
        if not extracted_text:
            raise ValueError("Document AI returned no text.")
        print("Text extraction successful.")
        
        response = requests.post(
            PRIVACY_SHIELD_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"text": extracted_text})
        )
        response.raise_for_status()
        sanitized_json = response.json()
        print(f"Service responded successfully: {sanitized_json}")

        # --- CHANGE #2: Save the full JSON and the sanitized text ---
        doc_ref.update({
            "status": "COMPLETED",
            "sanitized_text": sanitized_json.get("sanitized_text"),
            "document_ai_json": document_ai_json,
            "processed_at": firestore.SERVER_TIMESTAMP
        })
        print("Successfully saved to Firestore.")

    except Exception as e:
        print(f"An error occurred: {e}")
        doc_ref.update({"status": "ERROR", "error_message": str(e)})