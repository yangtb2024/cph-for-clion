## 项目简介

`cph-for-clion` 是一个用于自动化设置和测试竞赛编程题目的工具集，专为 CLion 用户设计。`cp-setup.py` 用于从 Competitive Companion 浏览器扩展获取题目信息，并自动创建项目目录，生成代码模板，并保存时间和空间限制。`run_tests.py` 用于编译和运行这些项目中的测试用例，同时尊重每个题目的时间限制和内存限制。

## 更新日志

最新版本：v0.2.1 - 2024年8月20日

[查看更新日志](https://blog.yangtb2024.me/archives/27)

## 文件结构

- `cp-setup.py`：从 Competitive Companion 获取题目并创建项目目录，保存相关信息，并生成 `main.cpp` 和测试用例文件。
- `run_tests.py`：编译项目代码并运行测试用例，根据 `limits.txt` 中的限制条件执行测试，并支持代码变更检测以提高效率。
- `latest_problem.txt`：保存最近获取的题目名称，用于快速定位项目目录。
- `limits.txt`：每个项目目录下保存的时间和空间限制文件。

## 安装与配置

### 先决条件

- **Python 3.x**
- **g++**：用于编译 C++ 代码。
- **Competitive Companion 浏览器扩展**：可以在 [Chrome Web Store](https://chrome.google.com/webstore/detail/competitive-companion/cjnmckjndlpiamhfimnnjmnckgghkjbl) 或 [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/competitive-companion/) 中获取。

### 安装依赖

确保你的环境中已经安装了 Python 和 g++ 编译器。

### 在 CLion 中配置 External Tools

1. 打开 CLion 并进入项目设置：
   - 选择 `File` > `Settings` (Windows/Linux) 或 `CLion` > `Preferences` (macOS)。

2. 配置 `cp-setup.py` 作为 External Tool：
   - 在左侧菜单中找到 `Tools` > `External Tools`。
   - 点击右侧的 `+` 号来添加一个新的工具。
   - 配置如下：
     - **Name**: `CP Setup`
     - **Program**: `python` 或 `python3`（取决于你的环境）
     - **Arguments**: `"$ProjectFileDir$/cp-setup.py"`
     - **Working directory**: `"$ProjectFileDir$"`
   - 点击 `OK` 保存配置。

3. 配置 `run_tests.py` 作为 External Tool：
   - 同样在 `Tools` > `External Tools` 中添加一个新工具。
   - 配置如下：
     - **Name**: `Run Tests`
     - **Program**: `python` 或 `python3`
     - **Arguments**: `"$ProjectFileDir$/run_tests.py"`
     - **Working directory**: `"$ProjectFileDir$"`
   - 点击 `OK` 保存配置。

## 使用教程

### 1. 获取题目并创建项目目录

在 CLion 中使用 `CP Setup` External Tool 来获取题目并创建项目目录：

- 选择 `Tools` > `External Tools` > `CP Setup`，这会启动一个 HTTP 服务器，等待 Competitive Companion 扩展发送题目信息。

打开浏览器中的编程竞赛网站，并使用 Competitive Companion 扩展将题目发送到你的服务器。`cp-setup.py` 会自动创建一个新目录，其中包含以下内容：

- `main.cpp`：带有题目信息的 C++ 代码模板。
- `inputX.txt` 和 `outputX.txt`：自动生成的测试用例。
- `limits.txt`：题目的时间和空间限制。

### 2. 编译代码并运行测试

在 CLion 中使用 `Run Tests` External Tool 来编译代码并运行测试用例：

- 选择 `Tools` > `External Tools` > `Run Tests`，它会自动使用 `latest_problem.txt` 中保存的最新题目名称来定位项目目录，并编译代码和运行测试用例。

运行后，你会看到 CLion 的控制台输出每个测试用例的结果。如果设置了时间和内存限制，程序会根据这些限制控制每个测试用例的运行时间和内存使用情况。

## 示例

假设你从 Competitive Companion 获取了一个题目 "Sample Problem"，文件结构如下：

```
Sample_Problem/
├── main.cpp
├── input1.txt
├── input2.txt
├── output1.txt
├── output2.txt
└── limits.txt
```

`limits.txt` 可能包含以下内容：

```
TimeLimit: 2000 ms
MemoryLimit: 256 MB
```

使用 `Run Tests` 工具将编译 `main.cpp` 并依次运行 `inputX.txt` 文件中定义的测试用例，结果会显示在 CLion 的控制台中，并在 `run_tests.log` 中记录详细信息。

## 注意事项

- 确保你的 C++ 代码能够从标准输入读取数据，并将结果输出到标准输出。
- 目前的工具不支持自动化的内存限制控制。如果需要严格控制内存使用，可以考虑使用操作系统的工具或其他编程语言实现此功能。

## 贡献

欢迎提交 issue 和 pull request 来改进这个项目。

## 许可证

该项目使用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。
