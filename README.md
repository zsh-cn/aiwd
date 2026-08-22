# AI 文档批量生成工具

基于 Python + Tkinter 的桌面应用程序，通过调用 OpenAI 兼容格式的 API，根据用户输入的创作主题，批量生成指定数量的 Markdown 文档，并自动转换为排版精美的 Word（.docx）文件。

## 功能特性

- **灵活的 API 配置**：支持任意 OpenAI 兼容端点（OneAPI、NewAPI、Azure 兼容地址等）
- **标题批量生成**：AI 根据主题自动生成多个文章标题，支持手动编辑、拖拽排序
- **文档批量生成**：遍历标题列表，逐个生成完整 Markdown 文档并转换为 .docx
- **AI 智能排版**：AI 分析文档结构（标题层级、列表、表格、代码块等），自动生成最佳排版方案
- **排版方案预览**：可自定义参考模板（reference-doc），或由 AI 生成专属模板
- **丰富的样式配置**：支持字体、字号、颜色、对齐、缩进、表格边框、页眉页脚、页码等精细控制
- **Pandoc 扩展参数**：支持目录生成（--toc）、章节编号（--number-sections）、代码高亮等高级功能
- **字数控制**：可指定每篇文档的目标字数
- **进度可视化**：进度条 + 状态提示，生成过程清晰可见
- **失败重试**：自动重试 + 指数退避，提高生成成功率
- **配置加密**：API Key 加密存储，保障安全

## 环境要求

- Python 3.9+
- Windows / macOS / Linux
- pandoc（`pypandoc_binary` 会在 pip 安装时自动打包 pandoc 二进制文件，无需单独安装）

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 打包

### 方式一：一键脚本（Windows）

项目根目录提供了 `dabao.bat` 一键打包脚本，自动创建虚拟环境、安装依赖并使用 PyInstaller 构建：

```bat
dabao.bat
```

执行后在 `dist/` 目录下生成 `AI_Doc_Generator.exe`。

### 方式二：手动打包

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AI_Doc_Generator" main.py
```

> 打包时若遇到 pandoc 或 httpx 资源缺失，可参照 `dabao.bat` 中的 `--hidden-import` 与 `--collect-all` 参数补齐。

## 使用说明

1. 点击右上角「设置」，配置 API 参数（Base URL、API Key、Model）
2. 输入创作主题和备注（可选）
3. 设置生成数量、目标字数和输出目录
4. 在「高级选项」中可配置：
   - **AI 智能排版**：启用后 AI 会分析文档结构并自动生成排版方案
   - **参考模板**：可指定一个已有的 .docx 作为参考模板（未指定则使用 AI 生成的模板）
5. 点击「生成标题列表」，AI 将自动生成标题
6. 可手动编辑标题、拖拽排序、删除不需要的标题
7. 点击「开始生成」，工具将逐个生成文档并转换为 .docx
8. 生成完成后点击「打开输出目录」查看结果

## 项目结构

```
aiwd/
├── main.py                  # 程序入口
├── config.py                # 配置读写与加密（API、字数、排版开关等）
├── api_client.py            # OpenAI 兼容 API 封装
├── title_generator.py       # 标题生成逻辑
├── doc_generator.py         # 文档批量生成（含线程管理、字数/排版控制）
├── converter.py             # Markdown 转 Docx（基于 pandoc）
├── ai_formatter.py          # AI 智能排版分析：结构识别 + 排版方案生成
├── template_generator.py    # Word reference-doc 模板生成（样式、页面、页眉页脚等）
├── dabao.bat                # 一键打包脚本（Windows）
├── AI_Doc_Generator.spec    # PyInstaller 打包配置（可选）
├── ui/
│   ├── main_window.py       # 主窗口
│   ├── settings_dialog.py   # 设置对话框
│   └── widgets.py           # 自定义控件（标题列表等）
├── utils/
│   ├── file_utils.py        # 文件命名、路径处理
│   └── prompt_templates.py  # Prompt 模板集中管理
├── requirements.txt
└── README.md
```

## 技术栈

- **GUI**：Python 标准库 `tkinter`
- **AI 接口**：`httpx` 异步/同步 HTTP 客户端
- **文档生成**：`pypandoc_binary` + pandoc
- **Word 模板**：`python-docx`
- **并发控制**：`threading` + `Event`
- **配置加密**：基于密钥派生的对称加密

## 主要流程

1. 用户在主界面输入主题、数量、字数等参数
2. `title_generator` 调用 AI 生成标题列表
3. 用户确认标题后，`doc_generator` 为每篇标题：
   - 调用 AI 生成 Markdown 正文（按字数控制）
   - 如启用 AI 排版，`ai_formatter` 分析文档结构并生成 JSON 排版方案
   - `template_generator` 根据排版方案生成 reference-doc 模板
   - `converter` 使用 pandoc 将 Markdown 转换为带样式的 .docx
4. 转换结果输出到用户指定目录

## License

MIT