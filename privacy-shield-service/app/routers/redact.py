from fastapi import APIRouter, HTTPException
from google.cloud import dlp_v2
from models import RedactionRequest, RedactionResponse
import os
import traceback # <--- ADD THIS IMPORT

router = APIRouter()
dlp_client = dlp_v2.DlpServiceClient()
GCP_PROJECT = os.getenv("GCP_PROJECT", "graphic-nucleus-470014-i6")

@router.post("/redact", response_model=RedactionResponse)
async def redact_text(request: RedactionRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    try:
        parent = f"projects/{GCP_PROJECT}/locations/global"
        info_types = [{"name": "PERSON_NAME"}, {"name": "EMAIL_ADDRESS"}, {"name": "PHONE_NUMBER"}, {"name": "STREET_ADDRESS"}, {"name": "INDIA_PAN_INDIVIDUAL"}, {"name": "INDIA_AADHAAR_INDIVIDUAL"}]
        deidentify_config = {"info_type_transformations": {"transformations": [{"primitive_transformation": {"replace_with_info_type_config": {}}}]}}
        item = {"value": request.text}
        dlp_request = {"parent": parent, "item": item, "deidentify_config": deidentify_config, "inspect_config": {"info_types": info_types}}
        response = dlp_client.deidentify_content(request=dlp_request)
        return RedactionResponse(sanitized_text=response.item.value)
    except Exception as e:
        # --- ADD THIS LINE FOR DEBUGGING ---
        traceback.print_exc()
        # -----------------------------------
        raise HTTPException(status_code=500, detail=f"An error occurred during PII redaction: {e}")
