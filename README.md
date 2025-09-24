#### INTER#LS 邀请你参与完善本条目

# IslandCaller NEXT - 随机进化
ICNEXT是一款基于Python语言开发的课堂效率工具合集，旨在为高效课堂提供新颖且实用的工具。

## 特性

- **轻量简洁：** 无需安装，下载解压即可使用，删除文件即可卸载；
- **简单配置：** 在您的大屏下载宿主软件ClassIsland（NotifyIsland插件）即可连接使用；
- **可配置性：** 接口开放，您可根据接口自行设计客户端，进一步定制您的专属课堂。

## 使用方法（以NotifyIsland为例）

1. **下载插件：** 安装ClassIsland，并从ClassIsland插件商店下载 `NotifyIsland` 插件。

2. **开启悬浮窗：** 在插件设置中启用端口（默认为`5002`，或者自行创建一个新端口，请自行修改源码）

3. **创建班级名单：** 在记事本中输入你的班级名单，每行一个`学生姓名`+`空格`+`0`，并保存为`std.namesbook`并保存到程序目录。

4. **安装Python依赖：** 安装Python13，并在终端中使用pip安装相应依赖：`pip install <name>`

5. **运行程序：** 至此你已经完成所有步骤，你可以通过运行`main.py`开启ICNEXT。

## 注意事项

- 确保 ICNEXT 及 ClassIsland 以管理员身份运行，否则可能出现端口注册失败的问题
- 确保 NotifyIsland 与程序源码中的端口设置匹配。

## 致谢

本项目依赖于以下项目：
- ClassIsland
- NotifyIsland

---

如果你在使用过程中遇到任何问题，欢迎提交 [Issue](https://github.com/Teak75035/ClassCaller-Server-Python/issues)。

---
