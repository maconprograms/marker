from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from pathlib import Path
import tempfile
import shutil
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

app = FastAPI(title="Marker OCR API")

# Create temp directories
UPLOAD_DIR = Path("./uploads")
RESULTS_DIR = Path("./results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

@app.post("/process")
async def process_pdf(
    file: UploadFile = File(...),
    output_format: str = Form("json"),
    use_llm: bool = Form(False),
    force_ocr: bool = Form(False)
):
    """Process a PDF file with Marker OCR"""
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Configure Marker
        config = {
            "output_format": output_format,
            "use_llm": use_llm,
            "force_ocr": force_ocr
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
        
        # Clean up
        os.remove(file_path)
        
        return result.dict()
        
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