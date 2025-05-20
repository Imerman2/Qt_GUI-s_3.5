import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QScrollArea, QLabel, QFrame)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import segno
from PIL import Image
import io
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

class QRCodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Generator Prototype")
        self.setGeometry(100, 100, 800, 600)

        # The Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: white")
        self.main_layout.addWidget(self.scroll_area)

        # Frame to Hold Generated QR Codes
        self.qr_frame = QFrame()
        self.qr_frame.setStyleSheet("background-color: white")
        self.scroll_area.setWidget(self.qr_frame)

        # Vertical layout for QR codes (This is AI generated code, idk what this exactly means)
        self.qr_layout = QVBoxLayout(self.qr_frame)

        #The lists I'll generate codes from
        self.links = ["https://example.com/1",
                      "https://example.com/2",
                      "https://example.com/3"] * 1000

        
        self.generate_qr_codes()
    
    def generate_qr_code(self, link):
        #Generating a single QR code from a single link
        try:
            qr = segno.make(link ,error = 'H')
            img_buffer = io.BytesIO()
            qr.save(img_buffer, kind='png', scale =5, border = 2)
            img_buffer.seek(0)
            return link, img_buffer.getvalue()
        except Exception as e:
            print(f"Error generating QR code for {link}: {e}")
            return link, None
    
    def generate_qr_codes(self):
        #Generate QR codes in parallel 
        start_time = time.time()

        #Do the work in parallel
        with ThreadPoolExecutor(max_workers = 3) as executor:
            results = list(executor.map(self.generate_qr_code, self.links))

        #Display the QR Codes
        for link, img_data in results:
            if img_data:
                #Convert to QPixMap
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)

                #Make a label for the QR code
                qr_label = QLabel()
                qr_label.setPixmap(pixmap)
                qr_label.setAlignment(Qt.AlignCenter)

                #Make a label for the link
                text_label = QLabel(link)
                text_label.setAlignment(Qt.AlignCenter)

                #Add to Layout
                self.qr_layout.addWidget(qr_label)
                self.qr_layout.addWidget(text_label)

        self.qr_layout.addStretch()

        print(f"Generated and displayed QR Codes in {time.time() - start_time:.2f} seconds")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QRCodeApp()
    window.show()
    sys.exit(app.exec_())

