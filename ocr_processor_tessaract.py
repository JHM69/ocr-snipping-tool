import pytesseract
from PIL import Image 
from path_manager import PathManager
import os

class TesseractOCR:
    """A class to handle OCR operations using Tesseract"""
    
    def __init__(self, tesseract_path):
        # Initialize PathManager
        self.path_manager = PathManager()
        print("Path is ", tesseract_path)
        if not os.path.exists(tesseract_path):
            raise FileNotFoundError(f"Tesseract executable not found at {tesseract_path}. Please check your installation.")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text(self, image, language): 
        """Extract text from the given image using Tesseract"""
        try:
            print("Lang is : ", language)
            pil_image = Image.fromarray(image)
            # Set the language for Tesseract
            text = pytesseract.image_to_string(pil_image, lang=language) 
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return ""

    def verify_tesseract(self):
        """Verify Tesseract installation and configuration"""
        try:
            # Try to get Tesseract version
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract version: {version}")
            print(f"Using Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
            return True
        except Exception as e:
            print(f"Tesseract verification failed: {str(e)}")
            print(f"Current Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
            return False