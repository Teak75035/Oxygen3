import sys
import os
import requests
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QPixmap

class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._is_dragging = False
        self._drag_position = QPoint()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(200, 100)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 204); border-radius:10px;")

        btn = QPushButton('', self)
        btn.setGeometry(10, 5, 160, 80)
        icon = QIcon(QPixmap("icon.png"))
        btn.setIcon(icon)
        btn.setIconSize(btn.size())
        btn.clicked.connect(self.run_app)

        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 40
        y = screen.height() - self.height() - 60
        self.move(x, y)

    def run_app(self):
        post_send()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        

def get_content_from_server(server: str, port: int, path: str = "/"):
    url = f"http://{server}:{port}{path}"
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def get_value_from_json(json_text: str, key: str):
    data = json.loads(json_text)
    return data.get(key)

def notification(title: str, title_duration: int, title_voice: str,
                 content: str, content_duration: int, content_voice: str):
########请确保端口设置正确！#########
    url = "http://127.0.0.1:5002/api/notify"
########请确保端口设置正确！#########
    data = {
        "title": title,
        "title_duration": title_duration,
        "title_voice": title_voice,
        "content": content,
        "content_duration": content_duration,
        "content_voice": content_voice
    }

    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

def post_send():
    server = "127.0.0.1"  #默认本地地址，按需修改
    port = 5001  #端口号
    path = "/rna"  # 可以根据需要修改
    content = get_content_from_server(server, port, path)
    data = get_value_from_json(content, "data")  # 先获取 data 字段
    value = None
    if isinstance(data, dict):  # 如果 data 是字典，直接取 name
        name_field = data.get("name")
        if isinstance(name_field, list) and len(name_field) > 0:
            value = name_field[0]
        elif isinstance(name_field, str):
            value = name_field
    if value is not None and isinstance(value, str) and len(value) > 0:
        notification(
            title=value,
            title_duration=3,
            title_voice=value,
            content="",
            content_duration=0,
            content_voice=""
        )
    else:
        print("未获取到有效的 name 字段，无法发送通知。")
        print("获取的内容:", data.get("name"))
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = FloatingWindow()
    win.show()
    sys.exit(app.exec_())
