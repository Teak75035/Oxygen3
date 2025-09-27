import sys
import subprocess
import requests
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QPixmap
import webbrowser
import os


class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._is_dragging = False
        self._drag_position = QPoint()
        self.setMouseTracking(True)  # 确保窗口接收鼠标事件
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(225, 75)
        self.setStyleSheet("background-color: rgba(50, 50, 50, 180); border-radius:10px;")

        # 按钮定义
        btn = QPushButton('', self)
        btn.setGeometry(7, 4, 67, 67)
        icon = QIcon(QPixmap("icon.png"))
        btn.setIcon(icon)
        btn.setIconSize(btn.size() * 0.7)  # 缩小图标到原来的85%
        btn.setStyleSheet("border: none; background-color: rgba(50, 50, 50, 180); border-top-left-radius: 10px; border-bottom-left-radius: 10px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;")
        btn.setAttribute(Qt.WA_TransparentForMouseEvents)
        btn.clicked.connect(self.run_none)

        icon2 = QIcon(QPixmap("icon2.png"))
        btn2 = QPushButton('', self)
        btn2.setGeometry(74, 4, 67, 67)
        btn2.setIcon(icon2)
        btn2.setIconSize(btn2.size() * 0.7)
        btn2.setStyleSheet("border: none; background-color: rgba(50, 50, 50, 180); border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;")
        btn2.clicked.connect(self.run_app)

        icon3 = QIcon(QPixmap("icon3.png"))
        btn3 = QPushButton('', self)
        btn3.setGeometry(141, 4, 67, 67)
        btn3.setIcon(icon3)
        btn3.setIconSize(btn3.size() * 0.7)
        btn3.setStyleSheet("border: none; background-color: rgba(50, 50, 50, 180); border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 10px; border-bottom-right-radius: 10px;")
        btn3.clicked.connect(self.run_new)


        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 30
        y = screen.height() - self.height() - 45
        self.move(x, y)

    def run_none(self):
        pass

    def run_new(self):
        new()

    def run_app(self):
        post_send()

    def mousePressEvent(self, event):
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
    print("[Hower] Status Code:", response.status_code)
    print("[Hower] Response Body:", response.text)

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
        print(f"[Hower] 未获取到有效的 name 字段，无法发送通知。")
        print("[Hower] 获取的内容:", data.get("name"))
        
def new():
    html_path = os.path.abspath("ol.html")
    webbrowser.open(f'file://{html_path}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = FloatingWindow()
    win.show()
    sys.exit(app.exec_())
