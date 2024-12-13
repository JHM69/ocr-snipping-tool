from PIL import Image
import google.generativeai as genai
from typing import Union
import numpy as np
import os
from dotenv import load_dotenv
from path_manager import PathManager

class GeminiOCR:
    """A class to handle OCR operations using Google's Gemini Pro Vision API"""
    
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self.api_key = self._get_api_key()
        self.model_name = 'gemini-1.5-pro'  # Use the correct model name
        self.initialize_api()
    
    def _get_api_key(self) -> str:
        """Retrieve the API key from environment variables"""
        path_manager = PathManager()  # Create an instance of PathManager
        api_key = path_manager.get_gemini_api_key  # Use the new method
        return api_key
    
    def initialize_api(self) -> None:
        """Initialize the Gemini API with the API key"""
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def convert_to_pil_image(self, image: Union[np.ndarray, Image.Image]) -> Image.Image:
        """Convert numpy array to PIL Image if necessary"""
        if isinstance(image, np.ndarray):
            return Image.fromarray(image)
        elif isinstance(image, Image.Image):
            return image
        else:
            raise ValueError("Input must be either a numpy array or PIL Image")
    
    def extract_text(self, image: Union[np.ndarray, Image.Image], language: str) -> str:
        """
        Extract text from the given image using Gemini Vision API
        
        Args:
            image: Input image as numpy array or PIL Image
            language: Selected language for OCR
            
        Returns:
            str: Extracted text from the image
        """
        try:
            # Convert image to PIL format and save as PNG
            pil_image = self.convert_to_pil_image(image)
            pil_image.save('temp.png', 'PNG')
            png_image = Image.open('temp.png')
            
            # Prepare the prompt for multilingual text extraction
            prompt = f"Whats written in this image in {language}. Give me only the OCR text."
            
            # Generate content using the model
            response = self.model.generate_content([prompt, png_image])
        
            # Extract and clean the text
            if response.text:
                return response.text.strip()
            return ""
        except ValueError as ve:
            print(f"Image conversion error: {str(ve)}")
            raise
        except Exception as e:
            print(f"Text extraction failed: {str(e)}")
            raise
    
    def verify_connection(self) -> bool:
        """
        Verify the connection to Gemini API
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Test the API with a simple prompt
            test_model = genai.GenerativeModel('gemini-pro')  # Use text-only model for testing
            response = test_model.generate_content("Test connection")
            return True
        except Exception as e:
            print(f"API connection verification failed: {str(e)}")
            return False

