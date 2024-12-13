# OCR Snipping Tool
# A snipping tool to Extract Text By snipping using cursor from anywhere on the screen.

Demo
![Demo](/demo.gif)

Home
![Home](/s1.png)

Setting
![Setting](/s2.png)

## Setup Guide

### Requirements
- Python 3.x
- PyQt5
- Pillow
- OpenCV
- NumPy
- pytesseract
- pyperclip3

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/JHM69/bangla_ocr_snippin_tool.git
   cd bangla_ocr_snippin_tool
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Tesseract Setup:**
   - **Windows:**
     1. Download the Tesseract installer from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
     2. Install Tesseract and note the installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
   - **Linux:**
     1. Install Tesseract using the package manager:
        ```bash
        sudo apt install tesseract-ocr
        ```

4. **Run the application:**
   - Launch the application by running:
   ```bash
   python main.py
   ```

5. **Set API Key and Tesseract Path:**
   - Once the application is running, you can enter the Tesseract path and Gemini API key in the provided input fields in the UI.
   - Click the "Save" button to store these settings.

6. **Using the Tool:**
   - Press `Ctrl + N` to create a new snip.
   - Press `Q` to quit the application.

### OCR Engine and Language Settings
- You can select between Tesseract and Gemini OCR engines from the dropdown menu in the application.
- You can also select the language for OCR from the settings tab.
- Supported languages include English, Bangla, Hindi, Japanese, Spanish, French, German, Chinese (Simplified), Russian, and Arabic.
