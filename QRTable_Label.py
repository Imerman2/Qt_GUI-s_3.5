import sys
import segno
import io
import numpy as np
import concurrent.futures
import time
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QTableWidget, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("QR Code Table Scroller With Proper Sized QR Codes (Hopefully)")
            self.setGeometry(100, 100, 800, 600)

            #QScroll Area
            scroll_area = QScrollArea(self)
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setSizeAdjustPolicy(QScrollArea.AdjustIgnored)

            #Create Content Widget
            content_widget = QWidget()
            scroll_area.setWidget(content_widget)

            #Create QVBoxLayout
            layout = QVBoxLayout(content_widget)
            layout.setAlignment(Qt.AlignTop)
            layout.setSpacing(10)

            #Create QTable Widget
            self.table = QTableWidget()
            layout.addWidget(self.table)

            #Set the main window's central widget
            self.setCentralWidget(scroll_area)

            #Hardcoded list of URLS (3 multiplied)
            self.urls = (
                ["https://www.example.com/1"] * 3000 +
                ["https://www.example.com/2"] * 3000 +
                ["https://www.example.com/3"] * 3000 
            )
            assert len(self.urls) == 9000, "URL list length mismatch."

            #Add QR codes to a table (9000 QR codes, 3 columns)
            self.add_qr_codes(count=9000, columns = 3)
        except Exception as e:
            print(f"Error in __init__: {e}.")
            raise

    def generate_qr_code(self, index):
        """Generate a single QR code and return its pixmap and index"""
        try:
            start_time = time.time()

            #Use URL from the hardcoded list
            qr = segno.make(self.urls[index], micro = False)

            #save to BytesIO as png
            buffer = io.BytesIO()
            qr.save(buffer, kind = 'png', scale = 8, border = 1)

            #Convert to Pixmap
            pixmap = QPixmap()
            if not pixmap.loadFromData(buffer.getvalue()):
                raise ValueError(f"Failed to load pixmap for QR code {index}.")
            elapsed = time.time() - start_time

            #Print pixmap size
            print(f"QR {index} pixmap size: {pixmap.width()}x{pixmap.height()}")
            return pixmap, index, elapsed
        except Exception as e:
            print(f"Error generationg QR Code {index}: {e}.")
            return None, index, 0
        

    def add_qr_code(self, pixmap, index, columns):
        """Add a QR code to the table widget using Qlabel"""
        try:
            if pixmap is None:
                print(f"Skipping QR code {index} due to generation error.")
                return
            
            #Create a QLabel and put the pixmap on it
            label = QLabel()
            label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
            label.setAlignment(Qt.AlignCenter)

            #Set fixed sizes
            label.setFixedSize(150, 150)
            row = index // columns
            col = index % columns

            #Set QLabel as cell widget
            self.table.setCellWidget(row, col, label)
        except Exception as e:
            print(f"Error adding QR code {index}: {e}.")

    def add_qr_codes(self, count, columns):
        """Add multiple QR codes using threading (makes it look like it is doint it out of order, it is not)"""
        try:
            start_time = time.time()
            total_generation_time = 0

            #Configure QTable widget
            self.table.setRowCount(math.ceil(count/columns))
            self.table.setColumnCount(columns)
            self.table.setHorizontalHeaderLabels([f"Col {i+1}" for i in range(columns)])
            self.table.setShowGrid(False)

            #Set column width and row height
            cell_size = 160 #slightly bigger than the qr codes 150px
            for i in range(columns):
                self.table.setColumnWidth(i, cell_size)
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, cell_size)
            self.table.setStyleSheet("QTableWidget { padding: 5px; }")

            #Debug
            print(f"Row 0 height: {self.table.rowHeight(0)}.")
            print(f"Column 0 height: {self.table.columnWidth(0)}.")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                #Submit QR code generation tasks
                futures = [
                    executor.submit(self.generate_qr_code, i)
                    for i in range(count)
                ]

                #Process results in batches
                batch_size = 1000
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    pixmap, index, gen_time = future.result()
                    total_generation_time += gen_time
                    self.add_qr_code(pixmap, index, columns)

                    #Update UI according to batch sizes
                    if (i+1) % batch_size == 0:
                        self.table.parent().adjustSize() #Adjust size of widget (with batches? maybe this isnt working...)
                        QApplication.processEvents() #Keep things responsive or whatever

            #Final adjustments
            self.table.parent().adjustSize()

            #Print performance metrics
            elapsed = time.time() - start_time
            print(f"Total time: {elapsed:.2f} seconds.")
            print(f"QR code generation time: {total_generation_time:.2f} seconds.")
            print(f"Average generation time per QR: {total_generation_time/count*3000:.2f} ms.")
        except Exception as e:
            print(f"Error in add_qr_codes: {e}.")
            raise

if __name__ == "__main__":
    try:
        #Enable high-DPI scaling for high resolution displays
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}.")





