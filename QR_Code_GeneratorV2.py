from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QGridLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys
import segno
import io
import numpy as np
import concurrent.futures
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Layout")
        self.setGeometry(100, 100, 800, 600)

        # QScrollArea Creation
        scroll_area = QScrollArea(self)        
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizeAdjustPolicy(QScrollArea.AdjustIgnored)

        # Create Content Widget
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        #Make the content Widget have grid spacing
        self.layout = QGridLayout(content_widget)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)  #Gap between codes

        #Set the central widget
        self.setCentralWidget(scroll_area)

        self.urls = (
            ["https://www.example1.com"] * 1000 +
            ["https://www.example2.com"] * 1000 +
            ["https://www.example3.com"] * 1000 
            )

        #Add the Qr codes in a grid, takes count and columns
        self.add_qr_codes(count = 3000, columns = 3)

    def generate_qr_code(self, index):
        """Generate a single qrcode and Pixmap"""
        start_time = time.time()
        #Use url from hardcoded list
        qr = segno.make(self.urls[index], micro =False)
        #Save to BytesIO as PNG
        buffer = io.BytesIO()
        qr.save(buffer, kind='png', scale = 5, border = 1)
        #Convert to Pixmap
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        #Optional: Convert to numpy array (if needed for processing)
        #img = np.array(ar.png_data_url()) [would this do anything?  idk]
        elapsed = time.time() - start_time
        return pixmap, index, elapsed
    
    def add_qr_code(self, pixmap, index, columns):
        """Add a QR code to the grid layout."""
        label = QLabel()
        label.setPixmap(pixmap.scaled(100,100, Qt.KeepAspectRatio))
        row = index // columns
        col = index % columns
        self.layout.addWidget(label, row, col)

    def add_qr_codes(self, count, columns):
        """Add multiple QR Codes using threads for efficiency (usually not much efficiency)"""
        start_time = time.time()
        total_generation_time = 0

        #Concurrent.futures for parallel cpu usage which maybe gives a boost idk
        with concurrent.futures.ThreadPoolExecutor() as executor:
            #Submit QR Code generation task
            futures = [
                executor.submit(self.generate_qr_code, i)
                for i in range(count)
            ]

            #Process these bitches in batches because waiting 14 seconds for 3000 QR codes is kind of annoying.
            batch_size = 100
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                pixmap, index, gen_time = future.result()
                total_generation_time += gen_time
                self.add_qr_code(pixmap, index, columns)

                #Update UI according to batch size
                if (i+1) % batch_size == 0:
                    self.layout.parentWidget().adjustSize()
                    QApplication.processEvents() #Keep UI responsive

        #Final size adjustment
        self.layout.parentWidget().adjustSize()

        #Print performance metrics
        elapsed = time.time() - start_time
        print(f"Total time: {elapsed:.2f} seconds.")
        print(f"QR code generation time: {total_generation_time:.2f} seconds.")
        print(f"Average generation time per QR: {total_generation_time/count*1000:.2f} ms.")


if __name__ == '__main__':
   app = QApplication(sys.argv)
   window = MainWindow()
   window.show()
   sys.exit(app.exec_())