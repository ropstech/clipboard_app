import sys
import time
import pyperclip
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal

# Clipboard history stored in memory
clipboard_history = {
    "All": [],
    "Text": [],
    "Numbers": [],
    "URLs": [],
    "Emails": []
}

class ClipboardMonitor(QThread):
    new_clipboard_entry = pyqtSignal(str, str)  # Signal sends entry text and category

    def __init__(self):
        super().__init__()
        self.running = False
        self.last_text = ""

    def run(self):
        self.running = True
        while self.running:
            current_text = pyperclip.paste()
            
            if current_text != self.last_text and current_text:
                self.last_text = current_text
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                category = self.categorize_content(current_text)
                
                # Emit the entry and category to update the GUI
                self.new_clipboard_entry.emit(f"{timestamp} - {current_text}", category)
                
                # Append to the "All" category and specific category
                clipboard_history["All"].append({"text": current_text, "timestamp": timestamp})
                clipboard_history[category].append({"text": current_text, "timestamp": timestamp})
            
            time.sleep(0.5)

    def stop(self):
        self.running = False
        self.wait()

    def categorize_content(self, content):
        if re.match(r'^[\d\s\.\-]+$', content) and sum(c.isdigit() for c in content) > len(content) / 2:
            return "Numbers"
        elif re.match(r'^(http|https)://', content):
            return "URLs"
        elif re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', content):  # Basic regex for emails
            return "Emails"
        else:
            return "Text"

class ClipboardHistoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Clipboard History")
        self.setGeometry(200, 200, 600, 500)

        # Main layout
        self.main_layout = QHBoxLayout()
        
        # Sidebar for categories
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # Frame to hold sidebar sections
        sidebar_frame = QFrame()
        sidebar_frame.setLayout(self.sidebar_layout)
        sidebar_frame.setFixedWidth(150)

        self.create_sidebar_buttons()

        # Right layout for history display
        self.history_layout = QVBoxLayout()
        
        self.label = QLabel("Clipboard History:")
        self.history_layout.addWidget(self.label)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.recopy_entry)
        self.history_layout.addWidget(self.history_list)

        # Clear and Exit buttons at the bottom
        self.clear_button = QPushButton("Clear History")
        self.exit_button = QPushButton("Exit")
        self.history_layout.addWidget(self.clear_button)
        self.history_layout.addWidget(self.exit_button)

        self.clear_button.clicked.connect(self.clear_history)
        self.exit_button.clicked.connect(self.exit_application)

        # Add sidebar and history display to the main layout
        self.main_layout.addWidget(sidebar_frame)
        self.main_layout.addLayout(self.history_layout, 3)

        self.setLayout(self.main_layout)

        # Clipboard monitoring thread
        self.monitor = ClipboardMonitor()
        self.monitor.new_clipboard_entry.connect(self.add_clipboard_entry)

        # Start clipboard monitoring automatically
        self.start_monitoring()

        self.show_startup_message()
        self.current_category = "All"
        self.display_history(self.current_category)

    def show_startup_message(self):
        print("Clipboard History Tracker started successfully.")

    def start_monitoring(self):
        self.monitor.start()

    def exit_application(self):
        self.monitor.stop()
        self.close()

    def create_sidebar_buttons(self):
        """Create sidebar buttons for each category."""
        categories = ["All", "Text", "Numbers", "URLs", "Emails"]

        # Add buttons in a vertical stack with spacing
        for category in categories:
            button = QPushButton(category)
            button.clicked.connect(lambda checked, cat=category: self.switch_category(cat))
            button.setFixedHeight(40)
            self.sidebar_layout.addWidget(button)
        
        # Add spacer at the bottom of sidebar
        self.sidebar_layout.addStretch()

    def switch_category(self, category):
        self.current_category = category
        self.display_history(category)

    def display_history(self, category):
        self.history_list.clear()
        for entry in clipboard_history[category]:
            item = QListWidgetItem(f"{entry['timestamp']} - {entry['text']}")
            self.history_list.addItem(item)

    def add_clipboard_entry(self, entry, category):
        if category == self.current_category or self.current_category == "All":
            self.history_list.addItem(entry)

    def clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History", "Are you sure you want to clear the clipboard history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for key in clipboard_history.keys():
                clipboard_history[key].clear()
            self.history_list.clear()
            #QMessageBox.information(self, "Info", "Clipboard history cleared.")

    def recopy_entry(self, item):
        entry_text = item.text().split(" - ", 1)[1]
        pyperclip.copy(entry_text)
        QMessageBox.information(self, "Copied", "Text copied back to clipboard.")

    def closeEvent(self, event):
        self.monitor.stop()
        event.accept()

# Main application setup
app = QApplication(sys.argv)
window = ClipboardHistoryApp()
window.show()
sys.exit(app.exec())
