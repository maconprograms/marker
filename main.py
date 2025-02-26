from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
import json
from pathlib import Path
import tempfile
import shutil
from google.cloud import storage
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

app = FastAPI(title="Marker OCR API")

# Initialize Google Cloud Storage client
storage_client = storage.Client()
BUCKET_NAME = "marker-icculus-storage"
bucket = storage_client.bucket(BUCKET_NAME)

# Create temp directories for local processing
UPLOAD_DIR = Path("./uploads")
RESULTS_DIR = Path("./results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Load default configuration
with open("config.json", "r") as f:
    DEFAULT_CONFIG = json.loads(f.read())

@app.post("/process")
async def process_pdf(
    file: UploadFile = File(...),
    output_format: str = Form(DEFAULT_CONFIG.get("output_format", "json")),
    use_llm: bool = Form(DEFAULT_CONFIG.get("use_llm", False)),
    force_ocr: bool = Form(DEFAULT_CONFIG.get("force_ocr", False))
):
    """Process a PDF file with Marker OCR"""
    
    # Generate unique ID for this request
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    try:
        # Save uploaded file locally first
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Upload to Cloud Storage
        blob = bucket.blob(f"uploads/{file_id}.pdf")
        blob.upload_from_filename(str(file_path))
        
        # Configure Marker
        config = {
            "output_format": output_format,
            "use_llm": use_llm,
            "force_ocr": force_ocr,
            "llm_service": DEFAULT_CONFIG.get("llm_service", {})
        }
        
        config_parser = ConfigParser(config)
        
        # Initialize converter
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service() if use_llm else None
        )
        
        # Process the PDF
        result = converter(str(file_path))
        
        # Store result in Cloud Storage if it contains images
        if hasattr(result, 'images') and result.images:
            for img_name, img_data in result.images.items():
                img_blob = bucket.blob(f"results/{file_id}/{img_name}")
                # Create a temporary file to store the image
                with tempfile.NamedTemporaryFile(delete=False) as temp_img:
                    temp_img.write(img_data)
                    temp_img_path = temp_img.name
                
                # Upload the image to Cloud Storage
                img_blob.upload_from_filename(temp_img_path)
                os.unlink(temp_img_path)  # Delete the temporary file
                
                # Update the image path in the result to point to Cloud Storage
                if output_format == "markdown":
                    # Replace local image references with Cloud Storage URLs
                    result.markdown = result.markdown.replace(
                        f"![{img_name}]({img_name})",
                        f"![{img_name}](https://storage.googleapis.com/{BUCKET_NAME}/results/{file_id}/{img_name})"
                    )
        
        # Store the result JSON in Cloud Storage
        result_blob = bucket.blob(f"results/{file_id}/result.json")
        result_blob.upload_from_string(
            data=result.json(),
            content_type="application/json"
        )
        
        # Add Cloud Storage URLs to the response
        response_data = result.dict()
        response_data["storage_urls"] = {
            "pdf": f"https://storage.googleapis.com/{BUCKET_NAME}/uploads/{file_id}.pdf",
            "result": f"https://storage.googleapis.com/{BUCKET_NAME}/results/{file_id}/result.json"
        }
        
        # Clean up local files
        os.remove(file_path)
        
        return response_data
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
