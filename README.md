📂 智能文件翻译 & 重命名工具 (Smart File Translator & Renamer)

一款Gemini编写的基于 Python 的现代化 GUI 工具，支持 AI 智能翻译、批量重命名、格式化清洗。专为 macOS 和 Windows 打造，拥有舒适的暗黑模式界面。

✨ 主要功能 (Features)

🎨 跨平台 & 暗黑模式：

自动识别 macOS 和 Windows 系统，适配最佳字体（Helvetica / Microsoft YaHei）。

精心调校的暗黑极简 UI，高对比度护眼配色，原生级体验。

🧠 双引擎翻译：

Google 翻译：内置免费接口，稳定快速，无需 API Key。

硅基流动 AI (SiliconFlow)：支持接入 DeepSeek、Qwen 等大模型，翻译更懂语境（需 API Key）。

支持自动获取模型列表，无需手动配置模型名称。

📝 灵活命名规则：

提供 纯英文、纯中文、中英混合 等多种命名格式。

自动清洗文件名：去除特殊字符、空格转下划线、统一小写。

🛠️ 批量工具箱：

无需翻译也能使用：文本替换、添加前后缀、自动序号生成、修改扩展名。

🛡️ 安全机制：

预览模式：所有操作先预览新文件名，确认无误再执行。

一键停止：随时中断耗时任务。

配置保存：自动保存 API Key 和模型选择，无需重复输入。

🚀 快速开始 (Quick Start)

1. 环境准备

确保你的电脑已安装 Python 3.8 或更高版本。

2. 安装依赖

打开终端 (Terminal) 或 CMD，运行以下命令安装必要的库：

pip install deep-translator requests


3. 运行工具

下载本项目代码，在终端中运行：

python file_translator.py


📖 使用指南 (Usage)

🅰️ 智能翻译模式

点击 "📂 选择文件夹"，加载需要处理的文件。

在 "智能翻译" 选项卡中选择引擎：

Google 翻译：开箱即用。

硅基流动 AI：输入 API Key，点击“刷新”选择模型（推荐 Qwen 或 DeepSeek）。

选择 命名格式（例如：纯英文）。

点击 "⚡ 生成预览"，等待翻译完成。

检查列表中的新文件名（双击可手动修改，右键可重试）。

点击底部的 "🚀 执行重命名"。

🅱️ 批量工具箱

如果你只需要简单整理文件，切换到 "🛠️ 批量工具" 选项卡：

文本替换：批量删除或替换文件名中的特定字符。

添加前后缀：如给所有图片加 2024_ 前缀。

自动序号：将乱序文件重命名为 img_001.jpg, img_002.jpg...

修改后缀：批量修改文件扩展名。

📦 如何打包 (Build)

如果你想生成 .exe (Windows) 或 .app (macOS) 发送给没有安装 Python 的朋友，可以使用 PyInstaller。

安装 PyInstaller

pip install pyinstaller


Windows 打包命令

pyinstaller --noconsole --onefile --name="智能翻译工具" file_translator.py


macOS 打包命令

pyinstaller --noconsole --onefile --windowed --name="SmartTranslator" file_translator.py


生成的程序将位于 dist 文件夹中。

⚠️ 注意事项

API Key 安全：你的 API Key 仅保存在本地的 translator_config.json 文件中，不会上传到任何服务器。

不可逆操作：虽然工具提供了预览功能，但在点击“执行”前，请务必确认文件名无误。建议对重要数据先进行备份。

📄 许可证

本项目采用 MIT 许可证。欢迎 Fork 和 Star！
