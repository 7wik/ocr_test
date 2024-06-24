"""
PDF to Text OCR Web Application

This Flask-based web application allows users to upload PDF files, extract a region of interest (ROI)
from the first page, perform Optical Character Recognition (OCR) using the Google Cloud Vision API, 
and return the extracted text in both plain and structured JSON formats.

Key Features:
- PDF Upload: Users can upload PDF files through a web interface.
- ROI Extraction: Extracts the top quadrant of the first page of the PDF.
- OCR Processing: Uses Google Cloud Vision API to perform OCR on the extracted ROI.
- Text Extraction: Returns extracted text as both plain text and JSON.
- Error Handling: Provides comprehensive error handling for robust operation.

Requirements:
- Python 3.x
- Flask
- PyMuPDF (fitz)
- Google Cloud Vision API client library
- Pillow (PIL)
- Google Cloud credentials

Setup and Usage:
1. Install dependencies.
2. Set up Google Cloud Vision API and obtain the credentials JSON file.
3. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of your credentials file.
4. Run the application using `python app.py`.
5. Access the web interface to upload PDF files and view OCR results.
"""


import os
import json
import re
from typing import Any
import logging
import fitz  # PyMuPDF
from google.cloud import vision
from PIL import Image
from flask import Flask, request, jsonify, render_template
from constants import IDENTIFIERS, GOOGLE_APPLICATION_CREDENTIALS_PATH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Set up your Google Cloud credentials
if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS_PATH):
    raise EnvironmentError("Google application credentials file not found.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS_PATH

def allowed_file(filename: str) -> bool:
    """
    Check if the file extension is allowed.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_roi_from_pdf(pdf_path: str) -> str:
    """
    Extract the region of interest (ROI) from the first page of a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The path to the saved image file of the extracted ROI.
    """
    try:
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(0)
        pix = page.get_pixmap()

        width, height = pix.width, pix.height
        img = Image.frombytes("RGB", [width, height], pix.samples)

        top_quadrant = img.crop((int(0.8 * width), int(0.09 * height), width, int(0.3 * height)))

        image_path = 'page_1_top_quadrant.png'
        top_quadrant.save(image_path, format='PNG')
        return image_path
    except Exception as e:
        logger.error(f"Error extracting ROI from PDF: {e}")
        raise RuntimeError(f"Error extracting ROI from PDF: {e}")

def ocr_from_image(image_path: str, client_obj: Any) -> str:
    """
    Perform OCR on a given image using the Google Cloud Vision API.

    Args:
        image_path (str): The path to the image file.
        client_obj (Any): The Google Cloud Vision API client object.

    Returns:
        str: The detected text from the image.
    """
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client_obj.text_detection(image=image)
        texts = response.text_annotations

        full_text = '\n'.join(text.description for text in texts)
        return full_text
    except Exception as e:
        logger.error(f"Error performing OCR on image: {e}")
        raise RuntimeError(f"Error performing OCR on image: {e}")

def extract_text_from_pdf(pdf_path: str, client_obj: Any) -> str:
    """
    Extract text from a PDF file by performing OCR on the extracted ROI of the first page.

    Args:
        pdf_path (str): The path to the PDF file.
        client_obj (Any): The Google Cloud Vision API client object.

    Returns:
        str: The detected text from the PDF.
    """
    try:
        image_path = extract_roi_from_pdf(pdf_path)
        text = ocr_from_image(image_path, client_obj)
        os.remove(image_path)  # Clean up the image file after processing
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise RuntimeError(f"Error extracting text from PDF: {e}")

def ocr_to_json(ocr: str) -> str:
    """
    Map OCR output to a JSON object of classes using regex patterns.

    Args:
        ocr (str): The OCR output text.

    Returns:
        str: A JSON string representing the mapped classes.
    """
    d = {f"class_{i}": None for i in range(len(IDENTIFIERS))}
    for i, c in enumerate(IDENTIFIERS):
        key = f"class_{i}"
        match = re.search(c, ocr)
        if match:
            d[key] = match.group(0).replace("\n", "-")
    return json.dumps(d)

@application.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """
    Handle PDF file uploads and process them to extract text using OCR.

    Returns:
        Response: A JSON response containing the OCR text and the mapped JSON object.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(file_path)
            client = vision.ImageAnnotatorClient()
            ocr_text = extract_text_from_pdf(file_path, client)
            ocr_json = ocr_to_json(ocr_text)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(file_path)  # Clean up the uploaded PDF file
        
        return json.loads(ocr_json)

    return jsonify({"error": "Invalid file format"}), 400

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@application.route('/')
def upload_form():
    """
    Render the file upload form.

    Returns:
        str: The rendered HTML template for the file upload form.
    """
    return render_template('upload.html')

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=8000)
