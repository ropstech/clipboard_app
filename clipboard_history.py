import sys
import time
import pyperclip
import re
import random
import string
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QFrame, QSlider, QDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class ClipboardMonitor(QThread):
    """Thread that monitors the clipboard."""
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
                self.new_clipboard_entry.emit(f"{timestamp} - {current_text}", category)

                clipboard_history["All"].append({"text": current_text, "timestamp": timestamp})
                clipboard_history[category].append({"text": current_text, "timestamp": timestamp})
            
            time.sleep(0.5)

    def stop(self):
        self.running = False
        self.wait()

    def categorize_content(self, content):
        """Categorize the clipboard content into categories like 'Numbers', 'URLs', 'Emails', and 'Text'."""
        if re.match(r'^[\d\-\+\/\.\,]+$', content):  # Majority numbers and separators
            return "Numbers"
        elif re.match(r'^(http|https)://', content):
            return "URLs"
        elif re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', content):
            return "Emails"
        else:
            return "Text"


class PasswordGeneratorDialog(QDialog):
    """Dialog window for generating passwords."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Generator")
        self.setGeometry(200, 200, 300, 200)

        # Initialize layout and widgets
        layout = QVBoxLayout()

        self.length_slider_label = QLabel("Password Length: 8")
        layout.addWidget(self.length_slider_label)

        # Add a slider to select password length
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(8, 32)
        self.length_slider.setValue(8)
        self.length_slider.valueChanged.connect(self.update_slider_label)
        layout.addWidget(self.length_slider)

        # Add a label to show the generated password
        self.password_label = QLabel("Generated Password: ")
        layout.addWidget(self.password_label)

        # Add Generate Password Button
        self.generate_button = QPushButton("Generate Password")
        self.generate_button.clicked.connect(self.generate_password)
        layout.addWidget(self.generate_button)

        # Add a button to regenerate a password with the same length
        self.regenerate_button = QPushButton("Regenerate Password")
        self.regenerate_button.clicked.connect(self.regenerate_password)
        layout.addWidget(self.regenerate_button)

        # Add Copy Button to copy the generated password to clipboard
        self.copy_button = QPushButton("Copy Password")
        self.copy_button.clicked.connect(self.copy_password_to_clipboard)
        layout.addWidget(self.copy_button)

        # Set layout
        self.setLayout(layout)

    def update_slider_label(self):
        """Update the slider label to show current password length"""
        self.length_slider_label.setText(f"Password Length: {self.length_slider.value()}")

    def generate_password(self):
        """Generate a random password with the selected length and display it"""
        self.password = self.create_password(self.length_slider.value())
        self.password_label.setText(f"Generated Password: {self.password}")

    def regenerate_password(self):
        """Regenerate a new password with the same length as the last one"""
        length = len(self.password) if hasattr(self, 'password') else self.length_slider.value()
        self.password = self.create_password(length)
        self.password_label.setText(f"Generated Password: {self.password}")

    def copy_password_to_clipboard(self):
        """Copy the currently shown password to the clipboard"""
        if hasattr(self, 'password'):
            pyperclip.copy(self.password)
            QMessageBox.information(self, "Copied", "Password copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Password", "No password generated yet!")

    def create_password(self, length):
        """Utility function to create a random password of the specified length"""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for i in range(length))



class ClipboardHistoryApp(QWidget):
    """Main application class."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipboard History")
        self.setGeometry(200, 200, 600, 500)

        # Initialize clipboard history
        global clipboard_history
        clipboard_history = {"All": [], "Text": [], "Numbers": [], "URLs": [], "Emails": []}

        # Initialize the main layout
        main_layout = QHBoxLayout(self)

        # --- Sidebar Layout ---
        self.sidebar_layout = QVBoxLayout()
        self.create_sidebar_buttons()

        # Add the sidebar to the main layout
        sidebar_frame = QFrame()
        sidebar_frame.setLayout(self.sidebar_layout)
        sidebar_frame.setFrameShape(QFrame.Shape.StyledPanel)
        main_layout.addWidget(sidebar_frame)

        # --- Main content area ---
        self.history_list = QListWidget()
        main_layout.addWidget(self.history_list)

        # Clipboard monitoring thread
        self.monitor = ClipboardMonitor()
        self.monitor.new_clipboard_entry.connect(self.add_clipboard_entry)
        self.monitor.start()

        # Show startup message
        self.show_startup_message()

    def create_sidebar_buttons(self):
        """Create sidebar buttons for each category."""
        # --- Password Generator Button ---
        password_button = QPushButton("Password Generator")
        password_button.clicked.connect(self.open_password_generator)
        self.sidebar_layout.addWidget(password_button)

        # Create the remaining clipboard category buttons
        categories = ["All", "Text", "Numbers", "URLs", "Emails"]

        # Add buttons in a vertical stack with spacing
        for category in categories:
            button = QPushButton(category)
            button.clicked.connect(lambda checked, cat=category: self.switch_category(cat))
            self.sidebar_layout.addWidget(button)

        # Add spacer at the bottom of sidebar
        self.sidebar_layout.addStretch()

    def open_password_generator(self):
        """Open the password generator dialog."""
        self.password_dialog = PasswordGeneratorDialog()
        self.password_dialog.exec()

    def switch_category(self, category):
        """Switch between clipboard categories."""
        self.history_list.clear()
        for entry in clipboard_history[category]:
            self.history_list.addItem(f"{entry['timestamp']} - {entry['text']}")

    def add_clipboard_entry(self, entry, category):
        """Add a new clipboard entry to the history list and update the current category."""
        clipboard_history["All"].append({"text": entry.split(" - ", 1)[1], "timestamp": entry.split(" - ", 1)[0]})
        clipboard_history[category].append({"text": entry.split(" - ", 1)[1], "timestamp": entry.split(" - ", 1)[0]})

        # If in the current category view, show the new entry
        if category == "All" or category == self.history_list.currentItem():
            self.history_list.addItem(entry)

    def show_startup_message(self):
        """Display a message when the program starts."""
        print("Clipboard History Tracker started successfully.")

    def closeEvent(self, event):
        """Handle application close event to ensure thread stops."""
        self.monitor.stop()
        event.accept()


# Main application setup
app = QApplication(sys.argv)
window = ClipboardHistoryApp()
window.show()
sys.exit(app.exec())
