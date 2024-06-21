import os
from typing import Any, List
import json
import re
import fitz  # PyMuPDF
from google.cloud import vision
from PIL import Image
from flask import Flask, request, jsonify, render_template
from constants import IDENTIFIERS, GOOGLE_APPLICATION_CREDENTIALS_PATH

application = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Set up your Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS_PATH

def extract_roi_from_pdf(pdf_path: str) -> str:
    """
    Function to crop the ROI from the PDF file
    """
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    # Presuming that the logo to be extracted is in the first page of the PDF
    page = pdf_document.load_page(0)
    pix = page.get_pixmap()

    width, height = pix.width, pix.height
    img = Image.frombytes("RGB", [width, height], pix.samples)

    # Crop the top quadrant of the image
    width, height = img.size
    top_quadrant = img.crop((int(0.8 * width), int(0.09 * height), width, int(0.3 * height)))

    # Save the cropped image
    image_path = 'page_1_top_quadrant.png'
    top_quadrant.save(image_path, format='PNG')
    return image_path

def ocr_from_image(image_path: str, client_obj: Any) -> str:
    """
    Function to perform OCR given an image path
    """
    # Read the image file
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client_obj.text_detection(image=image)
    texts = response.text_annotations

    # Extract the detected text
    full_text = ''
    for text in texts:
        full_text += text.description + '\n'
    return full_text

def extract_text_from_pdf(pdf_path: str, client_obj: Any) -> str:
    """
    Main function to perform OCR given a pdf path
    """
    # Convert PDF pages to top quadrant images
    image_path = extract_roi_from_pdf(pdf_path)

    # Perform OCR on each image and collect results
    full_text = ''
    text = ocr_from_image(image_path, client_obj)
    full_text += text + '\n'
    os.remove(image_path)  # Clean up the image file after processing
    return full_text

def ocr_to_json(ocr: str) -> str:
    """
    Map ocr output to a json object of classes
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
    print(request.files,"++++++++++++++")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        
        client = vision.ImageAnnotatorClient()
        ocr_text = extract_text_from_pdf(file_path, client)
        ocr_json = ocr_to_json(ocr_text)
        
        os.remove(file_path)  # Clean up the uploaded PDF file
        
        return jsonify({"ocr_text": ocr_text, "ocr_json": json.loads(ocr_json)})
# from flask import Flask, request, render_template, redirect, url_for


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/')
def upload_form():
    return render_template('upload.html')
if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    application.run(debug=True, port=8000)