📂 Smart Rename Pro (智能文件翻译 & 重命名工具)

v10.2 最新版 - 专为 macOS 和 Windows 打造的现代化、AI 驱动的文件批量处理神器。

✨ 核心亮点 (Highlights)

Smart Rename Pro 不仅仅是一个重命名工具，它集成了最新的 AI 能力与现代化的软件设计：

🎨 现代化极简 UI：

多主题切换：内置 "极简白 (Modern Light)"、"深空灰 (Midnight Pro)" 等多套精美主题。

原生体验：完美适配 Windows 高分屏 (High-DPI) 与 macOS 原生菜单栏，拒绝模糊与违和感。

侧边栏导航：采用现代软件流行的侧边栏布局，操作逻辑更清晰。

🧠 双引擎智能翻译：

Google 翻译：多线程高并发架构，速度极快，免费稳定。

硅基流动 AI (SiliconFlow)：接入 DeepSeek、Qwen 等大语言模型。

智能防封：独创的动态单线程 + 随机延时机制，自动处理 429/403 速率限制，虽然慢但极其稳定。

结果清洗：自动去除 AI 废话和标点，只保留精准的文件名。

模型筛选：自动获取云端模型列表并过滤掉不可用的嵌入模型。

🛠️ 强大的批量工具箱：

无需翻译也能使用：文本替换、添加前后缀、自动序号生成。

支持递归扫描子文件夹，并保持目录结构不变。

提供 "仅音频文件" 过滤器，专为整理素材库设计。

🛡️ 安全与容错：

实时预览：所有操作先预览新文件名，确认无误再执行。

异常筛选：一键勾选 "⚠️ 只看错误项"，快速定位处理失败的文件。

配置记忆：自动保存 API Key、上次打开的文件夹和主题设置。

📥 下载与安装 (Installation)

方式一：直接下载 (推荐)

请前往本项目的 [可疑链接已删除] 下载打包好的应用程序，无需安装 Python 环境：

Windows: SmartRenamePro.exe

macOS: SmartRenamePro.dmg

方式二：源码运行

如果你是开发者，可以通过源码运行：

克隆仓库

git clone [https://github.com/YourUsername/Smart-Rename-Pro.git](https://github.com/YourUsername/Smart-Rename-Pro.git)
cd Smart-Rename-Pro


安装依赖

pip install deep-translator requests


运行

python file_translator.py


📖 使用指南 (User Guide)

1. 基础操作

点击左上角的 "📂 选择文件夹" (或使用 macOS 顶部菜单 "文件 -> 打开...") 加载文件。

在左侧底部的 "选项" 中，可以勾选 "递归子目录" 来扫描所有深层文件。

2. 智能翻译模式

切换到 "✨ 智能翻译模式"。

选择引擎：

Google：适合快速翻译普通词汇。

SiliconFlow (AI)：适合需要理解语境的翻译。输入 API Key 后点击 ⟳ 刷新并选择模型。

选择格式：如 "纯英文"、"中英混合" 等。

点击 "⚡ 生成预览"。

提示：AI 模式为了防止封号，速度会有意放慢，请耐心等待。

预览无误后，点击右下角的 "🚀 开始重命名"。

3. 批量工具箱

切换到 "🛠️ 批量工具箱"，可进行非翻译类的整理：

文本替换：支持批量删除或替换特定字符。

添加字符：在文件名前/后批量添加文字（如日期、标签）。

自动序号：将乱序文件重命名为 file_001, file_002 格式。

⚙️ API 配置 (AI 功能)

要使用 AI 翻译功能，你需要一个 硅基流动 (SiliconFlow) 的 API Key。

注册硅基流动账号。

创建 API Key (通常以 sk- 开头)。

在软件中填入 Key，配置会自动保存到本地 translator_config.json 文件中。

<img width="1100" height="900" alt="image" src="https://github.com/user-attachments/assets/66352863-2046-43d8-a0e0-58bd32c13ff5" />



📄 许可证 (License)

本项目基于 MIT License 开源。
欢迎提交 Issue 或 Pull Request 来帮助改进这个项目！
