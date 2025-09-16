import functions_framework
import requests
import json
from google.cloud import documentai, firestore

# --- Your Configuration: FILL THESE IN ---
GCP_PROJECT="graphic-nucleus-470014-i6"
GCP_REGION="us"
DOC_AI_PROCESSOR_ID="b9c81ca1e6e6b84d"
PRIVACY_SHIELD_URL="https://privacy-shield-service-141718440544.us-central1.run.app/redact"
# ----------------------------------------

# Initialize all clients
docai_client = documentai.DocumentProcessorServiceClient()
firestore_client = firestore.Client()
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
        # Step 1: Document AI Extraction
        gcs_uri = f"gs://{bucket}/{filename}"
        full_processor_name = docai_client.processor_path(GCP_PROJECT, GCP_REGION, DOC_AI_PROCESSOR_ID)
        request = documentai.ProcessRequest(
            name=full_processor_name,
            gcs_document=documentai.GcsDocument(gcs_uri=gcs_uri, mime_type="application/pdf")
        )
        result = docai_client.process_document(request=request)
        extracted_text = result.document.text
        
        if not extracted_text:
            raise ValueError("Document AI returned no text.")
        print("Text extraction successful.")
        
        # Step 2: Privacy Shield Redaction
        response = requests.post(
            PRIVACY_SHIELD_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"text": extracted_text})
        )
        response.raise_for_status()
        sanitized_json = response.json()
        print(f"Service responded successfully: {sanitized_json}")

        # Step 3: Save to Firestore
        doc_ref.update({
            "status": "COMPLETED",
            "sanitized_text": sanitized_json.get("sanitized_text"),
            "processed_at": firestore.SERVER_TIMESTAMP
        })
        print("Successfully saved to Firestore.")

    except Exception as e:
        print(f"An error occurred: {e}")
        doc_ref.update({"status": "ERROR", "error_message": str(e)})