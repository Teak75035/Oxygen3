# IslandCaller NEXT - 随机进化

ICNEXT 是一款基于 Python 开发的课堂效率工具合集，旨在为高效课堂提供新颖且实用的工具。

---

## 功能
>更多功能正在抓紧开发，如果您有好的建议，请开启 issue。

- 悬浮窗一键随机抽取学生
- ClassIsland 通知推送
- 随机数据统计图
- 不重复多人抽选
- 更多功能开发中...

---

## 特性

- **轻量简洁：** 无需安装，下载解压即可使用，删除文件即可卸载。
- **简单配置：** 在您的大屏下载宿主软件 ClassIsland（NotifyIsland 插件）即可连接使用。
- **可配置性：** 接口开放，您可根据接口自行设计客户端，进一步定制您的专属课堂。

---

## 使用方法（以 NotifyIsland 为例）

1. **下载插件：** 安装 ClassIsland，并从 ClassIsland 插件商店下载 `NotifyIsland` 插件。
2. **开启悬浮窗：** 在插件设置中启用端口（默认为 `5002`，或者自行创建一个新端口，请同步修改源码）。
3. **创建班级名单：** 在记事本中输入您的班级名单，每行一个 `学生姓名` + `空格` + `0`，并保存为 `std.namesbook` 文件，放置到程序目录。
4. **安装 Python 依赖：** 安装 Python 3.10 或更高版本，并在终端中运行以下命令安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
5. **运行程序：** 至此，您已经完成所有步骤，可以通过运行 `main.py` 启动 ICNEXT。

---

## 注意事项

- 确保 ICNEXT 及 ClassIsland 以管理员身份运行，否则可能出现端口注册失败的问题。
- 确保 NotifyIsland 与程序源码中的端口设置匹配。

---

## 致谢

本项目依赖于以下项目：

- [ClassIsland]
- [NotifyIsland]
---

如果您在使用过程中遇到任何问题，欢迎提交 [Issue](https://github.com/Teak75035/IslandCallerNEXT/issues)。
