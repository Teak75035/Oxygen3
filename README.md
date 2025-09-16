#### 该应用正在重构，你可以正常使用，但我们已停止接受来自 *alpha2.1.13* 版本的 issue。
#### 实现方式正在开发，您可以自行设计客户端使用。
#### INTER#LS 邀请你参与完善本条目，该条目正在重写中。以下内容已过时，不在具有相关效应，请以更新后的文件为准。

# ClassCaller

ClassCaller 是一个基于 ClassIsland 插件 IslandCaller 的轻量级点名服务提供端，用于在课堂上快速点名。

## 特性

- **统一管理：** 学校创建可配置的全校服务器即可统一管理全校信息。
- **简单配置：** Windows电脑下载ClassIsland - IslandCaller 即可连接使用。
- **可配置性：** 可根据JSON返回结果自行设计客户端。

## 使用方法（IslandCaller实现）

1. **下载插件：** 从 ClassIsland 插件商店下载 `IslandCaller` 插件。

2. **开启悬浮窗：**
   在插件设置中启用悬浮窗，或者自行创建一个指向 `classisland://plugins/IslandCaller/Run` 的快捷方式。

3. **创建班级名单：**
   在记事本中输入你的班级名单，每行一个学生姓名+空格+0，并保存为std.namesbook并保存到程序目录。

4. **运行快捷方式进行点名：**
   点击桌面上的悬浮窗，打开 `IslandCaller` 插件并进行点名。

## 注意事项

- 确保 ClassIsland 本体的“注册 Url 协议”设置已开启，否则无法通过快捷方式启动插件。
- 确保 ClassIsland 与学校服务器连接通畅。

## 致谢

本项目依赖于以下项目：
- ClassIsland
- IslandCaller

---

如果你在使用过程中遇到任何问题，欢迎提交 [Issue](https://github.com/Teak75035/ClassCaller-Server-Python/issues)。

---
