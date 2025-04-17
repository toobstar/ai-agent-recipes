# pdf_processor.py
import os
import io
import PyPDF2
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pytesseract
from datetime import datetime
import re

class PDFProcessor:
    """Process PDF files and extract text."""
    
    def __init__(self):
        self.cache = {}
        
    def extract_text(self, pdf_data: bytes) -> str:
        """Extract text from a PDF file."""
        pdf_file = io.BytesIO(pdf_data)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text() + "\n"
            
        return text
    
    def extract_images(self, pdf_data: bytes) -> List[Image.Image]:
        """Extract images from a PDF file for OCR processing."""
        # This is a simplified implementation
        # Real implementation would extract images from PDF
        # For this example, we'll skip this and focus on text extraction
        return []
    
    def is_invoice(self, text: str) -> bool:
        """Determine if a document is an invoice based on text content."""
        invoice_indicators = [
            'invoice', 'bill', 'payment', 'due date', 'total amount',
            'invoice number', 'invoice date', 'billed to', 'payment terms'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for indicator in invoice_indicators if indicator in text_lower)
        
        # If more than 3 indicators are found, consider it an invoice
        return matches >= 3
