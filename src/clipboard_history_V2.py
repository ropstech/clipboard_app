import sys
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer, Qt
import pyperclip
from functools import partial
from pathlib import Path
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SystemTrayApp(QApplication):
    def __init__(self, icon_path):
        super().__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)

        # Set dark theme stylesheet
        self.setStyleSheet(
            """
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: transparent;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QWidgetAction {
                background-color: transparent;
            }
        """
        )

        self.icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.clipboard_history = []
        self.max_display_length = 50  # Max characters for display

        self.last_clipboard_text = pyperclip.paste()

        # Timer to check clipboard changes
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(1000)  # Check every second

        self.create_menu_content()
        self.tray.setContextMenu(self.menu)

    def create_menu_content(self):
        """Creates the menu content"""
        self.menu.clear()

        # Search bar
        search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_widget.setLayout(search_layout)

        search_label = QLabel("Search")
        search_layout.addWidget(search_label)

        self.search_bar = QLineEdit()
        self.search_bar.setStyleSheet("padding: 5px; border-radius: 4px;")
        search_layout.addWidget(self.search_bar)

        search_layout.setContentsMargins(10, 5, 10, 5)
        search_widget.setFixedHeight(search_widget.sizeHint().height())

        search_action = QWidgetAction(self.menu)
        search_action.setDefaultWidget(search_widget)
        self.menu.addAction(search_action)

        self.menu.addSeparator()

        # Editor Button
        self.menu_item = QAction("Editor", self.menu)
        self.menu.addAction(self.menu_item)

        self.menu.addSeparator()

        # Clipboard History Label
        history_label = QLabel("Clipboard History:")
        history_label.setStyleSheet("font-weight: bold; padding: 5px;")
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.addWidget(history_label)
        history_layout.setContentsMargins(10, 5, 10, 5)

        history_action = QWidgetAction(self.menu)
        history_action.setDefaultWidget(history_widget)
        self.menu.addAction(history_action)

        # Scrollable Clipboard History Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(250, 200)  # Fixed size for consistent UI
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.history_container = QWidget()
        self.history_container.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)

        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_layout.setSpacing(5)
        self.history_layout.setContentsMargins(10, 5, 10, 5)

        self.scroll_area.setWidget(self.history_container)

        scroll_action = QWidgetAction(self.menu)
        scroll_action.setDefaultWidget(self.scroll_area)
        self.menu.addAction(scroll_action)

        self.menu.addSeparator()

        # Auto-insert toggle
        self.auto_insert_action = QAction("Automatic Insertion Disabled", self.menu)
        self.auto_insert_action.setCheckable(True)
        self.auto_insert_action.setChecked(False)
        self.menu.addAction(self.auto_insert_action)

        self.menu.addSeparator()

        # Quit Action
        self.quit_action = QAction("Quit Clipboard Chimp", self.menu)
        self.quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(self.quit_action)

    def check_clipboard(self):
        """Checks for new clipboard content and updates history"""
        current_clipboard_text = pyperclip.paste()
        if (
            current_clipboard_text
            and current_clipboard_text != self.last_clipboard_text
        ):
            self.last_clipboard_text = current_clipboard_text
            self.update_clipboard_history(current_clipboard_text)

    def update_clipboard_history(self, text):
        """Adds new clipboard entry to history and updates the UI"""
        if text.strip():
            if text in self.clipboard_history:
                self.clipboard_history.remove(text)  # Move to top if already in history
            self.clipboard_history.insert(0, text)

            self.update_clipboard_history_ui()

    def update_clipboard_history_ui(self):
        """Updates the UI to show the clipboard history inside the scroll area"""
        # Clear old entries
        for i in reversed(range(self.history_layout.count())):
            widget = self.history_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Add updated history
        for item in self.clipboard_history:
            display_text = (
                item
                if len(item) <= self.max_display_length
                else item[: self.max_display_length] + "..."
            )
            button = QPushButton(display_text)
            button.setStyleSheet(
                """
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    border: none;
                    border-radius: 4px;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """
            )
            button.clicked.connect(partial(self.copy_to_clipboard, item))
            self.history_layout.addWidget(button)

        # Ensure scrollbar appears when needed
        self.scroll_area.verticalScrollBar().setValue(0)

    def copy_to_clipboard(self, text):
        """Copies selected item back to the clipboard"""
        pyperclip.copy(text)
        self.last_clipboard_text = text

    def quit_app(self):
        """Stops the app"""
        self.timer.stop()
        self.tray.setVisible(False)
        self.quit()


if __name__ == "__main__":
    try:
        # Dynamically construct the path to the icon
        base_dir = Path(__file__).parent.parent  # Go up to project_folder
        icon_path = base_dir / "data" / "images" / "monkey_icon.png"

        # Verify the icon file exists
        if not icon_path.exists():
            logging.error(f"Icon file not found at: {icon_path}")
            # Optionally, provide a fallback icon or exit gracefully
            raise FileNotFoundError(f"Icon file not found at: {icon_path}")

        logging.info("Starting Clipboard Chimp application...")
        app = SystemTrayApp(
            str(icon_path)
        )  # Convert to string for compatibility with PyQt
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)
