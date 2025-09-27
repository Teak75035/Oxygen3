import os
import sys
import ctypes
import subprocess
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QEvent

# 隐藏 Windows 平台下的控制台窗口
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def create_tray_icon():
    app = QApplication(sys.argv)

    # 调试输出：确认 QApplication 已初始化
    print(f"[Tray] QApplication 已初始化。")

    # 创建系统托盘图标
    tray_icon = QSystemTrayIcon()
    icon_path = os.path.join(os.path.dirname(__file__), "icon2.png")  # 图标路径
    if not os.path.exists(icon_path):
        print(f"[Tray] 错误：未找到 icon2.png 文件。")
        sys.exit(1)
    tray_icon.setIcon(QIcon(icon_path))

    # 设置托盘图标的提示信息
    tray_icon.setToolTip("ICNEXT - 运行中\n点击退出Python进程状态")

    # 创建托盘菜单
    tray_menu = QMenu()
    exit_action = tray_menu.addAction("退出")  # 添加退出选项
    exit_action.triggered.connect(lambda: terminate_all_python_processes())  # 绑定退出操作

    tray_icon.setContextMenu(tray_menu)

    # 处理托盘图标的左键点击事件
    def on_tray_icon_activated(reason):
        if reason == QSystemTrayIcon.Trigger:  # 左键点击
            print(f"[Tray] 托盘图标被点击。")  # 调试输出

    tray_icon.activated.connect(on_tray_icon_activated)

    # 显示托盘图标
    tray_icon.show()

    # 调试输出：确认托盘图标已设置
    print(f"[Tray] 托盘图标已设置并运行。")
    # 启动应用程序事件循环
    print(f"[Tray] 启动 QApplication 事件循环。")
    sys.exit(app.exec_())

def terminate_all_python_processes():
    """
    终止所有 Python 进程。
    Windows 平台使用 taskkill 命令，其他平台使用 pkill。
    """
    if sys.platform == "win32":
        subprocess.call("taskkill /F /IM python.exe /T", shell=True)  # 强制终止所有 Python 进程
    else:
        subprocess.call("pkill -f python", shell=True)  # 终止所有 Python 进程

if __name__ == "__main__":
    create_tray_icon()  # 启动托盘图标

