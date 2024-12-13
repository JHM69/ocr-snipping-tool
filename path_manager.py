import os
from dotenv import load_dotenv
import google.generativeai as genai


class PathManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        load_dotenv()
        
        # Get paths from environment variables or set default paths if not provided
        self.tesseract_path = os.getenv('TESSERACT_PATH')  
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Validate paths
        self._validate_paths()
        
        self.api_key = self._get_api_key()
        genai.configure(api_key=self.api_key)
    
    def _validate_paths(self):
        # Check if paths exist
        if not os.path.exists(self.tesseract_path):
            raise FileNotFoundError(f"Tesseract executable not found at: {self.tesseract_path}")
        
    @property
    def get_tesseract_path(self):
        return self.tesseract_path
    
    @property
    def get_gemini_api_key(self):
        return self.gemini_api_key
    
    def save_paths(self, tesseract_path, gemini_api_key):
        with open('.env', 'a') as f:
            f.write(f'TESSERACT_PATH={tesseract_path}\n')
            f.write(f'GOOGLE_API_KEY={gemini_api_key}\n')
    
    def _get_api_key(self):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_API_KEY='):
                    return line.split('=')[1].strip()
        return None
    