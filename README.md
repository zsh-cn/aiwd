# AI 文档批量生成工具

基于 Python 的桌面应用程序，通过调用 OpenAI 兼容格式的 API，根据用户输入的创作主题，批量生成指定数量的 Markdown 文档并自动转换为 Word（.docx）格式。

## 功能特性

- **灵活的 API 配置**：支持任意 OpenAI 兼容端点（OneAPI、NewAPI、Azure 兼容地址等）
- **标题批量生成**：AI 根据主题自动生成多个文章标题，支持手动编辑、拖拽排序
- **文档批量生成**：遍历标题列表，逐个生成完整 Markdown 文档并转换为 .docx
- **进度可视化**：进度条 + 状态提示，生成过程清晰可见
- **并发控制**：可配置并发数，避免触发 API 速率限制
- **失败重试**：自动重试 + 指数退避，提高生成成功率
- **配置加密**：API Key 加密存储，保障安全

## 环境要求

- Python 3.9+
- pandoc（pypandoc 会自动安装 pandoc 二进制文件）

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 打包

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AI文档生成工具" main.py
```

## 使用说明

1. 点击右上角「设置」，配置 API 参数（Base URL、API Key、Model）
2. 输入创作主题和备注（可选）
3. 设置生成数量和输出目录
4. 点击「生成标题列表」，AI 将自动生成标题
5. 可手动编辑标题、拖拽排序、删除不需要的标题
6. 点击「开始生成」，工具将逐个生成文档并转换为 .docx
7. 生成完成后点击「打开输出目录」查看结果

## 项目结构

```
aiwd/
├── main.py                  # 程序入口
├── config.py                # 配置读写与加密
├── api_client.py            # OpenAI 兼容 API 封装
├── title_generator.py       # 标题生成逻辑
├── doc_generator.py         # 文档批量生成（含线程管理）
├── converter.py             # Markdown 转 Docx
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