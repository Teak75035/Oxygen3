import os
import sys
import ctypes
import subprocess
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QEvent

# Hide console window on Windows
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def create_tray_icon():
    app = QApplication(sys.argv)

    # Debugging output to confirm QApplication is running
    print(f"[Tray] QApplication initialized.")

    # Create the system tray icon
    tray_icon = QSystemTrayIcon()
    icon_path = os.path.join(os.path.dirname(__file__), "icon2.png")
    if not os.path.exists(icon_path):
        print(f"[Tray] Error: icon.png not found in the current directory.")
        sys.exit(1)
    tray_icon.setIcon(QIcon(icon_path))

    # Set tooltip for the tray icon
    tray_icon.setToolTip("ICNEXT - 运行中\n点击退出Python进程状态")

    # Create the tray menu
    tray_menu = QMenu()
    exit_action = tray_menu.addAction("退出")
    exit_action.triggered.connect(lambda: terminate_all_python_processes())

    tray_icon.setContextMenu(tray_menu)

    # Handle left-click event
    def on_tray_icon_activated(reason):
        if reason == QSystemTrayIcon.Trigger:  # Left-click
            print(f"[Tray] Tray icon clicked.")  # Debugging output

    tray_icon.activated.connect(on_tray_icon_activated)

    # Show the tray icon
    tray_icon.show()

    # Debugging output to confirm tray icon is set up
    print(f"[Tray] Tray icon is set up and running.")
    # Start the application event loop
    print(f"[Tray] Starting QApplication event loop.")
    sys.exit(app.exec_())

def terminate_all_python_processes():
    if sys.platform == "win32":
        subprocess.call("taskkill /F /IM python.exe /T", shell=True)
    else:
        subprocess.call("pkill -f python", shell=True)

if __name__ == "__main__":
    create_tray_icon()

