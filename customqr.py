import sys
import segno
import io
import numpy as np
import time
import hashlib
from pylibdmtx import pylibdmtx
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFormLayout, QComboBox,
                             QLineEdit, QPushButton, QLabel, QRadioButton, QFileDialog,
                             QVBoxLayout, QColorDialog, QMessageBox)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt

class QRMatrixGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customizable QR Code Generator")
        self.setGeometry(100, 100, 600, 500)

        #Central Widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        #Form layouts for inputs
        form_layout = QFormLayout()

        #Code type QR code or Data Matrix
        self.code_type_combo = QComboBox()
        self.code_type_combo.addItems(["QR Code", "Data Matrix"])
        form_layout.addRow("Code Type:", self.code_type_combo)

        #Data type (URL or SHA256 hash)
        self.url_radio = QRadioButton("URL")
        self.hash_radio = QRadioButton("SHA-256 Hash")
        self.url_radio.setChecked(True)
        form_layout.addRow("Data Type", self.url_radio)
        form_layout.addRow("", self.hash_radio)

        #Data input (URL or file path)
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("Enter URL or select file.")
        form_layout.addRow("File:", self.data_input)

        #File picker button for SHA256 Hash
        self.file_button = QPushButton("Select File")
        self.file_button.clicked.connect(self.select_file)
        form_layout.addRow("File:", self.file_button)

        #Size options (approximate module sizes)
        self.size_combo = QComboBox()
        size_options = ["19x19 (Small)", "23x23 (Medium)", "27x27 (Large)", "33x33 (Extra Large)"]
        self.size_combo.addItems(size_options)
        form_layout.addRow("Size", self.size_combo)

        #Error correction level
        self.error_combo = QComboBox()
        self.error_combo.addItems("Low", "Medium", "Quartile", "High")
        form_layout.addRow("Error Correction:", self.error_combo)

        #Color picker
        self.color_button = QPushButton("Choose Color.")
        self.color_button.clicked.connect(self.choose_color)
        self.color_label = QLabel ("Black (default).")
        self.color = Qt.black #Default black
        form_layout.addRow("Color:", self.color_button)
        form_layout.addRow("Selected Color:", self.color_label)

        #Generate button
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_code)
        form_layout.addRow(self.generate_button)

        #Display area for QR code/Data Matrix
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setMinimumSize(200, 200)

        #Save button
        self.save_button = QPushButton("Save Image")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False) #Disabled until the code is enabled.

        #Add layouts to the main layouts
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.display_label)
        main_layout.addWidget(self.save_button)
        main_layout.addStretch()

        #Generated Pixmap for saving
        self.pixmap = None

    #File picker
    def select_file(self):
        """Open file dialog to select a file for SHA-256 Hashing."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File.")
        if file_path:
            self.data_input.setText(file_path)
            self.hash_radio.setChecked(True)

    #Choose color self
    def choose_color(self):
        """Open color dialog to choose foreground color."""
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.color_label.setText(color.name())

    #Compute SHA-256, utilize proper chunks of data and ensure to code and decode properly.
    def compute_sha256(self, file_path):
        """Compute SHA 256 Hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
                return sha256.hexdigest()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to hash file: {e}.")
            return None
        
    def generate_code(self):
        """Generate QR code or Data Matrix based on user input"""
        start_time = time.time()

        #Get user inputs
        code_type = self.code_type_combo.currentText()
        is_url = self.url_radio.isChecked()
        data = self.data_input.text()
        size_index = self.size_combo.currentIndex()
        error_level = self.error_combo.currentText()
        color = self.color.name()

        #Validate input
        if not data:
            QMessageBox.warning(self, "Input Error", "Please enter a URL or select a file.")
            return
        
        #Handle data type
        if is_url:
            data_to_encode = data
        else:
            #Compute SHA256 hash
            data_to_encode = self.compute_sha256(data)
            if not data_to_encode:
                return
            
        #Map size to QR code version or Data Matrix size

        qr_versions = [1, 2, 3, 5] #Approx 19x19, 23x23, 27x27, 33x33
        dm_sizes = [(18, 18), (22, 22), (26, 26), (32, 32) ]
        version = qr_versions[size_index] if code_type == "QR Code" else None
        dm_size = dm_sizes[size_index] if code_type == "Data Matrix" else None
        
        #Map error correction
        error_map = {"Low": "L", "Medium": "M", "Quartile": "Q", "High": "H"}
        error = error_map[error_level] if code_type == "QR Code" else None

        try:
            #Generate QR code or Data Matrix
            buffer = io.BytesIO()
            if code_type == "QR Code":
                qr = segno.make(data_to_encode, micro = False, version = version, error = error)
                qr.save(buffer, kind = "png", scale = 8, dark = color, border = 1)
            else: #Data Matrix
                encoded = pylibdmtx.encode(data_to_encode.encode('utf-8'), size = dm_size)
                img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
                img = img.convert("RGBA")
                data = np.array(img)
                r, g, b = QColor(color).getRgb()[:3]
                black = (data[:, :, 0] == 0) & (data[:, :, 1] == 0) & (data[:, :, 2] == 0)
                data[black] = (r, g, b, 255)
                img = Image.fromarray(data)
                img.save(buffer, format='PNG')

            #Convert to QPixmap for display
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(buffer.getvalue())
            self.display_label.setPixmap(self.pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            self.save_button.setEnabled(True)

            #Print Performance
            elapsed = time.time() - start_time
            print(f"Generation time: {elapsed:.2f} seconds.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate code: {e}.")
            self.save_button.setEnabled(False)

    def save_image(self):
        """Save the generated QR code/Data Matrix as an image."""
        if not self.pixmap:
            QMessageBox.warning(self, "Error.", "No image to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png)")
        if file_path:
            self.pixmap.save(file_path, "PNG")
            QMessageBox.information(self, "Success", "Image saved successfully.")

if __name__ == "__main__":
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        app = QApplication(sys.argv)
        window = QRMatrixGenerator()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}.")
    
    
    

















