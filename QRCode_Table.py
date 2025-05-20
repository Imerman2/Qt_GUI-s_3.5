import sys
import segno
import io
import numpy as np
import concurrent.futures
import time
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Table Display")
        self.setGeometry(100, 100, 800, 600)

        #Create QScroll Area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizeAdjustPolicy(QScrollArea.AdjustIgnored)

        #Create Content Widget
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        #QVBoxLayout for vertically adding content with a scroll wheel when needed
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)

        #Create the QTable widget
        self.table = QTableWidget()
        layout.addWidget(self.table)

        #Set the main window's central widget
        self.setCentralWidget(scroll_area)

        #Hardcoded lists of URLs (3 multiplied)
        self.urls = (
            ["https://www.example.com/1"] * 3 +
            ["https://www.example.com/2"] * 3 +
            ["https://www.example.com/3"] * 3 
        )

        assert len(self.urls) == 9, "URL list length mismatch"

        #Add QR codes to table (9000 Qr codes 3 columns)
        self.add_qr_codes(count = 9, columns = 3)

    def generate_qr_code(self, index):
        """Generate a single QR code and its pixmap and index"""
        try:
            start_time = time.time()
            #Use urls from list
            qr = segno.make(self.urls[index], micro = False)
            #Save to Bytes IO as png
            buffer = io.BytesIO()
            qr.save(buffer, kind='png', scale = 7, border = 1)
            #Convert to Pixmap
            pixmap = QPixmap()
            if not pixmap.loadFromData(buffer.getvalue()):
                raise ValueError(f"Failed to load pixmap for QR code {index}.")
            elapsed = time.time() - start_time
            return pixmap, index, elapsed
        except Exception as e:
            print(F"Error generating QR code {index}: {e}.")

    def add_qr_code(self, pixmap, index, columns):
        """Add a QR code to the table widget."""
        try:
            if pixmap is None:
                print(f"Skipping QR code {index} due to generation error.")
                return
            
            item = QTableWidgetItem()
            item.setIcon(QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio)))
            item.setFlags(Qt.ItemIsEnabled) #Makes it non-editable
            row = index // columns
            col = index % columns
            self.table.setItem(row, col, item)
            print(f"Pixmap size for QR {index}: {pixmap.width()}x{pixmap.height()}.")
            
        except Exception as e:
            print(f"Error adding QR code {index}: {e}.")

    def add_qr_codes(self, count, columns):
        """Add multiple QR codes using cpu threads for better efficiency, maybe"""
        try: 
            start_time = time.time()
            total_generation_time = 0

            #Configure the table widget
            self.table.setRowCount(math.ceil(count / columns))  #Make enough rows for the QR codes
            self.table.setColumnCount(columns)
            self.table.setHorizontalHeaderLabels([f"Col{i+1}" for i in range(columns)])
            

            #Set column width
            for i in range(columns):
                self.table.setColumnWidth(i, 110)  #Pad the columns 110px vs qr code 100
            #Set row height
            row_height = 110
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, row_height)

            #Debug time bitches
            print(f"Row 0 height: {self.table.rowHeight(0)}.")
            print(f"Column 0 width: {self.table.columnWidth(0)}.")

            #Generate QR codes in parallel because we are cool [not cool enough to understand exactly how we are doing it though]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                #Submit QR code generation task
                futures = [
                    executor.submit(self.generate_qr_code, i)
                    for i in range(count)
                ]

                batch_size = 100
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    pixmap, index, gen_time = future.result()
                    total_generation_time += gen_time
                    self.add_qr_code(pixmap, index, columns)

                    #Update ui in batches
                    if (i+1) % batch_size == 0:
                        #self.table.resizeRowsToContents()
                        self.table.parent().adjustSize() #Adjust content widget size
                        QApplication.processEvents() #Keep UI Responsive

            #Final adjustments
            #self.table.resizeRowsToContents()
            #self.table.parent().adjustSize()

            #Print performance results
            elapsed = time.time() - start_time
            print(f"Total time: {elapsed:.2f} seconds.")
            print(f"QR code generation time: {total_generation_time:.2f} seconds.")
            print(f"Average generation time per QR: {total_generation_time/count*3000:.2f} ms.")
        
        except Exception as e:
            print(f"Error in add_qr_codes: {e}.")
            raise
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}.")








