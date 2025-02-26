import os
import runpod
import shutil
import tempfile
import base64
from pathlib import Path
import subprocess
import json

# Install Marker if needed (will run once when container starts)
def install_marker():
    try:
        import marker
        print("Marker already installed")
    except ImportError:
        print("Installing marker-pdf...")
        subprocess.check_call(["pip", "install", "marker-pdf"])
        print("Marker installed successfully")

# Run this when container starts
install_marker()

def process_file(file_path, output_format="json", use_llm=False, force_ocr=False):
    """Process a file with Marker and return the results"""
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    from marker.config.parser import ConfigParser
    
    # Create a temporary directory for output
    output_dir = tempfile.mkdtemp()
    
    # Configure Marker
    config = {
        "output_format": output_format,
        "output_dir": output_dir,
        "force_ocr": force_ocr,
        "use_llm": use_llm
    }
    
    # Enable LLM if requested and API key is available
    if use_llm and os.environ.get("GOOGLE_API_KEY"):
        config["use_llm"] = True
    else:
        config["use_llm"] = False
    
    # Set up the converter
    config_parser = ConfigParser(config)
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service() if config["use_llm"] else None
    )
    
    # Process the file
    print(f"Processing file: {file_path}")
    rendered = converter(file_path)
    
    # Extract results
    result = {}
    
    if output_format == "json":
        # For JSON, return the raw JSON
        result["output"] = rendered.model_dump()
        
        # Also extract images if any
        if hasattr(rendered, "images") and rendered.images:
            result["images"] = {}
            for img_id, img_data in rendered.images.items():
                result["images"][img_id] = base64.b64encode(img_data).decode("utf-8")
    else:
        # For markdown or HTML, extract the text and images
        text, _, images = text_from_rendered(rendered)
        result["text"] = text
        
        # Convert images to base64
        if images:
            result["images"] = {}
            for img_id, img_data in images.items():
                result["images"][img_id] = base64.b64encode(img_data).decode("utf-8")
    
    # Clean up
    shutil.rmtree(output_dir, ignore_errors=True)
    
    return result

def handler(job):
    """
    RunPod handler function for processing documents with Marker
    
    Input job format:
    {
        "input": {
            "file_url": "URL to download the file",
            "output_format": "json|markdown|html", (optional, default: json)
            "use_llm": true|false, (optional, default: false)
            "force_ocr": true|false (optional, default: false)
        }
    }
    """
    job_input = job["input"]
    
    # Get parameters
    file_url = job_input.get("file_url")
    output_format = job_input.get("output_format", "json")
    use_llm = job_input.get("use_llm", False)
    force_ocr = job_input.get("force_ocr", False)
    
    # Validate input
    if not file_url:
        return {"error": "No file_url provided"}
    
    # Create a temporary directory for the file
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Download the file
        file_name = os.path.basename(file_url.split("?")[0])
        file_path = os.path.join(temp_dir, file_name)
        
        print(f"Downloading file from {file_url}")
        # Use curl to download the file
        download_cmd = ["curl", "-L", "-o", file_path, file_url]
        subprocess.check_call(download_cmd)
        
        # Process the file
        if not os.path.exists(file_path):
            return {"error": f"Failed to download file from {file_url}"}
        
        result = process_file(file_path, output_format, use_llm, force_ocr)
        
        return result
    
    except Exception as e:
        import traceback
        error_msg = f"Error processing file: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {"error": error_msg}
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

# Start the serverless handler
runpod.serverless.start({"handler": handler})