import pytesseract
from PIL import Image
import pdfplumber
from docx import Document
import os

# Path to your installed tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(uploaded_file):
    image = Image.open(uploaded_file)
    text = pytesseract.image_to_string(image, config='--psm 6')
    return text

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs])

def clean_text(raw_text):
    text = raw_text.replace('\n', ' ')
    text = ' '.join(text.split())
    return text

