import sys
import json 
from datetime import datetime

import numpy as np
import pyperclip as pc
from PIL import ImageGrab
from dotenv import load_dotenv

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QLineEdit, QComboBox, QLabel, 
    QTabWidget, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QFrame, 
    QListWidgetItem, QTextEdit, QCheckBox
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont

from ocr_processor import GeminiOCR
from ocr_processor_tessaract import TesseractOCR
from path_manager import PathManager

load_dotenv()


class ConfigManager:
    """
    A helper class for reading and writing configuration settings
    to/from a .env file. Uses dictionary storage in memory for easy updates.
    """
    def __init__(self, env_file='.env'):
        self.env_file = env_file
        self.config = {}
        self.load()

    def load(self):
        """Load .env variables into self.config."""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
        except FileNotFoundError:
            # If no .env file yet, it's okay.
            pass

    def save(self):
        """Write the current config dictionary to the .env file."""
        try:
            with open(self.env_file, 'w') as f:
                for key, value in self.config.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print("Error saving .env file:", e)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = str(value)
        self.save()


class SnippingWidget(QtWidgets.QWidget):
    """
    A full-screen widget used to snip a portion of the screen.
    On mouse release, it captures the selected region and performs OCR.
    """
    num_snip = 0
    is_snipping = False
    background = True

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Default OCR engine and language
        self.ocr_engine = 'tesseract'
        self.language = 'eng'

        # Path Manager and keys
        self.path_manager = PathManager()
        self.tesseract_path = self.path_manager.get_tesseract_path
        self.gemini_api_key = self.path_manager.get_gemini_api_key

        # Get screen geometry via PyQt
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width, screen_height = screen_geometry.width(), screen_geometry.height()
        self.setGeometry(0, 0, screen_width, screen_height)

        self.begin = QPoint()
        self.end = QPoint()

    def start(self):
        """Start the snipping process."""
        if self.parent:
            self.parent.hide()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        SnippingWidget.background = False
        SnippingWidget.is_snipping = True
        self.setWindowOpacity(0.3)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        print('Capture the screen... Press Q to quit.')
        self.showFullScreen()
        self.show()

    def paintEvent(self, event):
        """
        Draw the selection rectangle while snipping.
        """
        if SnippingWidget.is_snipping:
            brush_color = (128, 128, 255, 100)
            line_width = 3
            opacity = 0.3
        else:
            self.begin = QPoint()
            self.end = QPoint()
            brush_color = (0, 0, 0, 0)
            line_width = 0
            opacity = 0

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), line_width))
        qp.setBrush(QtGui.QColor(*brush_color))
        rect = QtCore.QRectF(self.begin, self.end)
        qp.drawRect(rect)

    def keyPressEvent(self, event):
        """
        Press 'Q' to quit snipping without capturing.
        """
        if event.key() == QtCore.Qt.Key_Q:
            print('Quit snipping.')
            self.close()
        event.accept()

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        """
        On mouse release, capture the selected region and run OCR.
        """
        SnippingWidget.is_snipping = False

        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        self.repaint()

        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        try:
            img_np = np.array(img)
            # Refresh paths/keys
            self.path_manager = PathManager()
            self.tesseract_path = self.path_manager.get_tesseract_path
            self.gemini_api_key = self.path_manager.get_gemini_api_key

            if self.ocr_engine == 'tesseract':
                ocr_processor = TesseractOCR(tesseract_path=self.tesseract_path)
                text = ocr_processor.extract_text(img_np, self.language)
            elif self.ocr_engine == 'gemini':
                ocr_processor = GeminiOCR()
                text = ocr_processor.extract_text(img, self.language)
            else:
                text = ""
            
            print("Extracted text:", text)
            pc.copy(text)
        except Exception as e:
            print("Error during OCR:", e)
            text = ""

        if self.parent:
            self.parent.update_snip_results(text)

        if self.parent:
            self.parent.show()
            self.parent.raise_()
            self.parent.activateWindow()
        self.hide()

    def set_ocr_engine(self, engine, language):
        """Set the OCR engine and language."""
        self.ocr_engine = engine
        self.language = language


class SnipResultItem(QWidget):
    """
    Custom widget to represent a single snip result with time, text, 
    and copy/delete buttons.
    """
    def __init__(self, snippet_time, snippet_text, parent=None):
        super().__init__(parent)
        self.snippet_text = snippet_text
        self.snippet_time = snippet_time

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.time_label = QLabel(self.snippet_time)
        self.time_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.time_label)

        self.text_label = QLabel(self.snippet_text)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label, stretch=1)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_text)
        layout.addWidget(self.copy_button, alignment=Qt.AlignRight)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_text)
        layout.addWidget(self.delete_button, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def copy_text(self):
        pc.copy(self.snippet_text)
        print("Snippet copied to clipboard.")

    def delete_text(self):
        # Navigate up to the parent Menu and call delete_snip_result
        parent_menu = self.parentWidget()
        while parent_menu and not isinstance(parent_menu, Menu):
            parent_menu = parent_menu.parentWidget()
        if parent_menu:
            parent_menu.delete_snip_result(self.snippet_time)
        print("Snippet deleted.")


class Menu(QMainWindow):
    """
    Main Application Window for the OCR Snipping Tool.
    Manages OCR settings, snip results, and UI components.
    """
    default_title = "OCR Snipping Tool"

    def __init__(self, numpy_image=None, snip_number=None, start_position=(1200, 600, 800, 600)):
        super().__init__()

        self.title = Menu.default_title
        self.setWindowTitle(self.title)
        self.setGeometry(*start_position)

        self.total_snips = 0
        self.ocr_engine = 'tesseract'
        self.language = 'eng'

        self.config_manager = ConfigManager()

        # Determine background image
        if numpy_image is not None and snip_number is not None:
            self.image = self.convert_numpy_img_to_qpixmap(numpy_image)
        else:
            self.image = QPixmap("background.PNG")

        # Snipping tool instance
        self.snippingTool = SnippingWidget(parent=self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(20)

        self.new_snip_button = QPushButton("+ New Snip (Ctrl+N)")
        self.new_snip_button.setToolTip("Start a New Snip")
        self.new_snip_button.setShortcut("Ctrl+N")
        self.new_snip_button.setStyleSheet("""
            QPushButton {
                font-size: 25px; 
                font-weight: bold; 
                color: white; 
                background-color: #2E7D32; 
                border-radius: 25px; 
                width: 280px; 
                height: 50px;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        self.new_snip_button.clicked.connect(self.new_snip_window)
        top_bar.addWidget(self.new_snip_button, 0, Qt.AlignLeft)

        self.ocr_mode_selector = QComboBox()
        self.ocr_mode_selector.addItems(["Tesseract", "Gemini"])
        self.ocr_mode_selector.setToolTip("Select OCR Engine")
        self.ocr_mode_selector.currentIndexChanged.connect(self.update_ocr_mode)
        top_bar.addWidget(self.ocr_mode_selector, 0, Qt.AlignLeft)

        top_frame = QFrame()
        top_frame.setLayout(top_bar)
        main_layout.addWidget(top_frame, 0, Qt.AlignTop)

        # Tabs
        self.tab_widget = QTabWidget()
        self.ocr_tab = QWidget()
        self.about_tab = QWidget()
        self.settings_tab = QWidget()
        self.tab_widget.addTab(self.ocr_tab, "OCR Options")
        self.tab_widget.addTab(self.about_tab, "About")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        main_layout.addWidget(self.tab_widget)

        self.setup_ocr_tab()
        self.setup_about_tab()
        self.setup_settings_tab()

        self.load_existing_paths()
        self.load_existing_snip_results()

        self.show()

    def setup_ocr_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Snip Results
        layout.addWidget(QLabel("Snip Results:"))
        self.snip_results_list = QListWidget()
        layout.addWidget(self.snip_results_list, stretch=1)

        layout.addWidget(QLabel("Last Extracted Text:"))
        self.extracted_text_label = QTextEdit("")
        self.extracted_text_label.setStyleSheet("background: #F0F0F0; padding: 5px; border: 1px solid #CCC;")
        layout.addWidget(self.extracted_text_label)

        self.copy_extracted_text_button = QPushButton("Copy Last Extracted Text")
        self.copy_extracted_text_button.clicked.connect(self.copy_extracted_text)
        layout.addWidget(self.copy_extracted_text_button)

        self.ocr_tab.setLayout(layout)

    def setup_about_tab(self):
        layout = QVBoxLayout()

        # Title Label
        title_label = QLabel("<h1>OCR Snipping Tool</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Developer Info Section
        developer_label = QLabel(
            "<p>Developed by <strong>Jahangir Hossain</strong></p>"
            "<p><em>CSE, JnU</em></p>"
            "<p><a href='https://facebook.com/jhm69'>facebook.com/jhm69</a></p>"
        )
        developer_label.setAlignment(Qt.AlignCenter)
        developer_label.setOpenExternalLinks(True)
        layout.addWidget(developer_label)

        # GitHub Link Section
        github_label = QLabel(
            "<p><a href='https://github.com/jhm69' style='color: #0366d6;'>Visit Developer's GitHub</a></p>"
        )
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)

        # Repository Link Section
        repo_label = QLabel(
            "<p><a href='https://github.com/JHM69/ocr-snipping-tool' style='color: #0366d6;'>"
            "Go to Repository</a></p>"
            "<p>Star it and contribute via pull requests!</p>"
        )
        repo_label.setAlignment(Qt.AlignCenter)
        repo_label.setOpenExternalLinks(True)
        layout.addWidget(repo_label)

        self.about_tab.setLayout(layout)

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # OCR Settings Inputs
        layout.addWidget(QLabel("OCR Settings:"))

        self.tesseract_path_input = QLineEdit()
        self.tesseract_path_input.setPlaceholderText("Enter Tesseract Path")

        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setPlaceholderText("Enter Gemini API Key")

        layout.addWidget(self.tesseract_path_input)
        layout.addWidget(self.gemini_api_key_input)

        # Language Selection
        layout.addWidget(QLabel("Select Language:"))
        self.language_selector = QComboBox()
        languages = {
            'English': 'eng',
            'Bangla': 'ben',
            'Hindi': 'hin',
            'Japanese': 'jpn',
            'Spanish': 'spa',
            'French': 'fra',
            'German': 'deu',
            'Chinese (Simplified)': 'chi_sim',
            'Russian': 'rus',
            'Arabic': 'ara'
        }
        self.languages = languages
        self.language_selector.addItems(languages.keys())
        self.language_selector.setCurrentText("English")
        layout.addWidget(self.language_selector)

        # Save Text Setting
        self.save_text_checkbox = QCheckBox("Want to Save the Text")
        layout.addWidget(self.save_text_checkbox)

        # Old Text Limit Setting
        layout.addWidget(QLabel("How many old texts to save:"))
        self.old_text_limit_input = QLineEdit()
        self.old_text_limit_input.setPlaceholderText("Enter number of texts to save")
        layout.addWidget(self.old_text_limit_input)

        # Apply and Save Settings Button
        self.apply_settings_button = QPushButton("Apply Settings")
        self.apply_settings_button.setStyleSheet("padding: 5px;")
        self.apply_settings_button.clicked.connect(self.apply_ocr_settings)
        layout.addWidget(self.apply_settings_button)

        self.settings_tab.setLayout(layout)

    def new_snip_window(self):
        """Initiate a new snip."""
        self.total_snips += 1
        self.snippingTool.start()
        self.hide()

    def paintEvent(self, event):
        """
        Draw background image.
        """
        painter = QPainter(self)
        rect = QRect(0, 0, self.image.width(), self.image.height())
        painter.drawPixmap(rect, self.image)

    def closeEvent(self, event):
        event.accept()

    @staticmethod
    def convert_numpy_img_to_qpixmap(np_img):
        """
        Convert a NumPy image array to QPixmap.
        """
        height, width, channel = np_img.shape
        bytesPerLine = 3 * width
        return QPixmap(QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped())

    def set_ocr_engine(self, engine, language):
        """Set OCR engine and language both locally and in the snipping tool."""
        self.ocr_engine = engine
        self.language = language
        self.snippingTool.set_ocr_engine(engine, language)

    def save_paths(self):
        """
        Save Tesseract path and Gemini API key to the .env file via the config manager.
        """
        tesseract_path = self.tesseract_path_input.text()
        gemini_api_key = self.gemini_api_key_input.text()
        self.config_manager.set('TESSERACT_PATH', tesseract_path)
        self.config_manager.set('GOOGLE_API_KEY', gemini_api_key)
        print("Paths saved successfully.")

    def load_existing_paths(self):
        """
        Load existing paths from the .env file and set them into input fields.
        """
        tesseract_path = self.config_manager.get('TESSERACT_PATH', '')
        gemini_api_key = self.config_manager.get('GOOGLE_API_KEY', '')
        self.tesseract_path_input.setText(tesseract_path)
        self.gemini_api_key_input.setText(gemini_api_key)

    def update_snip_results(self, text):
        """
        Update the snip results list and save them if enabled.
        """
        self.show()
        self.extracted_text_label.setText(text)
        self.raise_()
        self.activateWindow()

        snip_results = self.load_snip_results()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        snip_results[current_time] = text

        save_text = self.config_manager.get('SAVE_TEXT', 'True').lower() == 'true'
        old_text_limit = int(self.config_manager.get('OLD_TEXT_LIMIT', '10'))

        if save_text:
            # Maintain limit of old texts
            if len(snip_results) > old_text_limit:
                oldest_key = list(snip_results.keys())[0]
                del snip_results[oldest_key]
            self.save_snip_results(snip_results)

        self.load_items_into_list(snip_results)

    def load_existing_snip_results(self):
        """
        Load existing snip results from JSON and show them in the UI.
        """
        try:
            snip_results = self.load_snip_results()
            self.load_items_into_list(snip_results)
        except FileNotFoundError:
            pass

    def load_snip_results(self):
        """Load snip results from the JSON file."""
        try:
            with open('snip_results.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_snip_results(self, snip_results):
        """Save snip results to the JSON file."""
        try:
            with open('snip_results.json', 'w') as f:
                json.dump(snip_results, f, indent=4)
        except Exception as e:
            print("Error saving snip results:", e)

    def load_items_into_list(self, snip_results):
        """
        Load snip result items into the QListWidget.
        """
        self.snip_results_list.clear()
        for snippet_time, snippet_text in snip_results.items():
            item_widget = SnipResultItem(snippet_time, snippet_text)
            list_item = QListWidgetItem(self.snip_results_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.snip_results_list.addItem(list_item)
            self.snip_results_list.setItemWidget(list_item, item_widget)

    def update_ocr_mode(self):
        """
        Called when OCR mode is changed from the combo box.
        """
        selected_mode = self.ocr_mode_selector.currentText()
        if (selected_mode == "Tesseract"):
            self.set_ocr_engine('tesseract', self.language)
            self.gemini_api_key_input.show()
            self.tesseract_path_input.show()
        elif (selected_mode == "Gemini"):
            self.set_ocr_engine('gemini', self.language)
            self.tesseract_path_input.show()
            self.gemini_api_key_input.show()

    def apply_ocr_settings(self):
        """
        Apply OCR settings from the UI to the configuration.
        """
        # Save paths from input fields
        self.save_paths()

        # Update language
        selected_lang = self.languages.get(self.language_selector.currentText(), 'eng')
        self.language = selected_lang

        # Update OCR Engine
        selected_mode = self.ocr_mode_selector.currentText().lower()
        self.set_ocr_engine(selected_mode, self.language)

        # Save text and limit
        save_text = self.save_text_checkbox.isChecked()
        old_text_limit = self.old_text_limit_input.text()
        if not old_text_limit.isdigit():
            old_text_limit = '10'  # fallback

        self.config_manager.set('SAVE_TEXT', str(save_text))
        self.config_manager.set('OLD_TEXT_LIMIT', old_text_limit)

        print("OCR Settings Applied.")
        print(f"OCR Engine: {self.ocr_engine}, Language: {self.language}")

    def delete_snip_result(self, snippet_time):
        """
        Delete a specific snip result by time from JSON storage and update list.
        """
        try:
            snip_results = self.load_snip_results()
            if snippet_time in snip_results:
                del snip_results[snippet_time]
            self.save_snip_results(snip_results)
            self.load_items_into_list(snip_results)
        except Exception as e:
            print("Error deleting snip result:", e)

    def copy_extracted_text(self):
        """Copy the currently displayed extracted text to the clipboard."""
        text = self.extracted_text_label.toPlainText()
        pc.copy(text)
        print("Last extracted text copied to clipboard.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainMenu = Menu()
    sys.exit(app.exec_())
