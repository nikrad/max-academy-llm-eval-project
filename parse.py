from PyPDF2 import PdfReader
from io import BytesIO
from docx import Document


# Function to process PDF
async def parse_pdf_file(file_content):
    pdf_reader = PdfReader(BytesIO(file_content))
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text


# Function to process text file
async def parse_text_file(file_content):
    return file_content.decode("utf-8")


# Function to process DOCX file
async def parse_docx_file(file_content):
    doc = Document(BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text
