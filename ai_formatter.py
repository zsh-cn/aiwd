"""AI 排版分析器 - 分析文档内容结构，生成排版配置"""

import json
import re

from api_client import APIClient, APIError


# AI 输出的排版配置 JSON Schema 说明
# {
#   "styles": {
#     "default_font": {"name": "宋体", "size": 11, "color": "#000000",
#                      "italic": false, "strike": false, "superscript": false,
#                      "subscript": false, "character_spacing": 0,
#                      "shadow": false, "outline": false,
#                      "emboss": false, "imprint": false, "glow": false},
#     "title": {"font": "黑体", "size": 22, "color": "#1a1a1a", "bold": true,
#               "alignment": "center", "space_before": 24, "space_after": 18,
#               "page_break_before": false, "page_break_after": false},
#     "h1" ~ "h6": {...},
#     "body": {"font": "宋体", "size": 11, "color": "#000000",
#              "line_spacing": 1.5, "first_line_indent": 22,
#              "tab_stops": []},
#     "quote": {...},
#     "list": {...},
#     "nested_list": {"level2": {...}, "level3": {...}},
#     "code": {"font": "Consolas", "size": 10, "color": "#2d3748",
#              "background_color": "#f7fafc", "left_indent": 20},
#     "inline_code": {"font": "Consolas", "size": 10, "color": "#2d3748",
#                     "background_color": "#f0f0f0"},
#     "hr": {"color": "#999999", "width": 1.0,
#            "space_before": 12, "space_after": 12},
#     "task_list": {"font": "宋体", "size": 11, "color": "#000000",
#                   "line_spacing": 1.4, "space_before": 3, "space_after": 3},
#     "definition": {"term_font": "黑体", "term_size": 11, "term_color": "#1a202c",
#                    "definition_font": "宋体", "definition_size": 11, "definition_color": "#000000",
#                    "left_indent": 44},
#     "table": {"font": "宋体", "size": 10, "color": "#000000",
#               "border": true, "border_color": "#000000", "border_width": 0.5,
#               "row_height": 0.8,
#               "cell_margin_top": 0.1, "cell_margin_bottom": 0.1,
#               "cell_margin_left": 0.1, "cell_margin_right": 0.1,
#               "cell_shading": "#f5f5f5"},
#     "link": {"font": "宋体", "size": 11, "color": "#3182ce", "underline": true},
#     "image": {"alignment": "center",
#               "caption_font": "宋体", "caption_size": 9, "caption_color": "#666666"},
#     "header": {"text": "", "font": "宋体", "size": 9, "color": "#666666",
#                "alignment": "center"},
#     "footer": {"text": "", "font": "宋体", "size": 9, "color": "#666666",
#                "alignment": "center", "page_number": true}
#   },
#   "page": {
#     "margin_top": 2.54, "margin_bottom": 2.54,
#     "margin_left": 3.18, "margin_right": 3.18,
#     "paper_size": "A4", "orientation": "portrait",
#     "columns": 1,
#     "page_border_color": "#000000", "page_border_width": 1.0,
#     "background_color": "#ffffff"
#   },
#   "footnotes": {"font": "宋体", "size": 9, "color": "#333333"},
#   "endnotes": {"font": "宋体", "size": 9, "color": "#333333"},
#   "pandoc_extra_args": [...]
# }


def _extract_json(content: str) -> dict:
    """从 AI 响应中提取 JSON 配置"""
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, content)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    cleaned = re.sub(r'```json\s*|\s*```', '', content)
    cleaned = re.sub(r'```\s*|\s*```', '', cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    raise ValueError(f"无法解析 AI 返回的排版配置: {content[:200]}...")


def _normalize_config(config: dict) -> dict:
    """将 AI 返回的配置规范化为标准格式，填充默认值"""
    defaults = {
        "styles": {
            "default_font": {
                "name": "宋体", "size": 11, "color": "#000000",
                "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "shadow": False, "outline": False,
                "emboss": False, "imprint": False, "glow": False,
            },
            "title": {
                "font": "黑体", "size": 22, "color": "#1a1a1a",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "shadow": False, "outline": False,
                "emboss": False, "imprint": False, "glow": False,
                "alignment": "center",
                "space_before": 24, "space_after": 18,
                "page_break_before": False, "page_break_after": False,
            },
            "h1": {
                "font": "黑体", "size": 18, "color": "#1a365d",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "alignment": "left",
                "space_before": 24, "space_after": 12,
                "page_break_before": False, "page_break_after": False,
            },
            "h2": {
                "font": "黑体", "size": 15, "color": "#2c5282",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "alignment": "left",
                "space_before": 20, "space_after": 10,
                "page_break_before": False, "page_break_after": False,
            },
            "h3": {
                "font": "黑体", "size": 13, "color": "#2b6cb0",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "alignment": "left",
                "space_before": 16, "space_after": 8,
                "page_break_before": False, "page_break_after": False,
            },
            "h4": {
                "font": "黑体", "size": 12, "color": "#3182ce",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "shadow": False, "outline": False,
                "emboss": False, "imprint": False, "glow": False,
                "alignment": "left",
                "space_before": 14, "space_after": 6,
                "page_break_before": False, "page_break_after": False,
            },
            "h5": {
                "font": "黑体", "size": 11, "color": "#4299e1",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "shadow": False, "outline": False,
                "emboss": False, "imprint": False, "glow": False,
                "alignment": "left",
                "space_before": 12, "space_after": 6,
                "page_break_before": False, "page_break_after": False,
            },
            "h6": {
                "font": "黑体", "size": 10.5, "color": "#63b3ed",
                "bold": True, "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "shadow": False, "outline": False,
                "emboss": False, "imprint": False, "glow": False,
                "alignment": "left",
                "space_before": 10, "space_after": 4,
                "page_break_before": False, "page_break_after": False,
            },
            "body": {
                "font": "宋体", "size": 11, "color": "#000000",
                "italic": False, "strike": False,
                "superscript": False, "subscript": False,
                "character_spacing": 0,
                "line_spacing": 1.5, "first_line_indent": 22,
                "tab_stops": [],
            },
            "quote": {
                "font": "楷体", "size": 11, "color": "#4a5568",
                "italic": False, "strike": False,
                "left_indent": 44, "right_indent": 44,
                "space_before": 6, "space_after": 6,
            },
            "list": {
                "font": "宋体", "size": 11, "color": "#000000",
                "italic": False, "strike": False,
                "line_spacing": 1.4,
                "space_before": 3, "space_after": 3,
            },
            "nested_list": {
                "level2": {
                    "font": "宋体", "size": 10.5, "color": "#333333",
                    "italic": False, "strike": False,
                    "line_spacing": 1.3, "left_indent": 22,
                },
                "level3": {
                    "font": "宋体", "size": 10, "color": "#555555",
                    "italic": False, "strike": False,
                    "line_spacing": 1.2, "left_indent": 22,
                },
            },
            "code": {
                "font": "Consolas", "size": 10, "color": "#2d3748",
                "italic": False, "strike": False,
                "background_color": "#f7fafc",
                "left_indent": 20, "right_indent": 20,
                "space_before": 6, "space_after": 6,
                "line_spacing": 1.2,
            },
            "inline_code": {
                "font": "Consolas", "size": 10, "color": "#2d3748",
                "italic": False, "strike": False,
                "background_color": "#f0f0f0",
            },
            "hr": {
                "color": "#999999", "width": 1.0,
                "space_before": 12, "space_after": 12,
            },
            "task_list": {
                "font": "宋体", "size": 11, "color": "#000000",
                "italic": False, "strike": False,
                "line_spacing": 1.4,
                "space_before": 3, "space_after": 3,
            },
            "definition": {
                "term_font": "黑体", "term_size": 11, "term_color": "#1a202c",
                "term_bold": True,
                "definition_font": "宋体", "definition_size": 11, "definition_color": "#000000",
                "definition_italic": False,
                "left_indent": 44,
            },
            "table": {
                "font": "宋体", "size": 10, "color": "#000000",
                "italic": False, "strike": False,
                "border": True, "border_color": "#000000",
                "border_width": 0.5,
                "row_height": 0.8,
                "cell_margin_top": 0.1, "cell_margin_bottom": 0.1,
                "cell_margin_left": 0.1, "cell_margin_right": 0.1,
                "cell_shading": "",
            },
            "link": {
                "font": "宋体", "size": 11, "color": "#3182ce",
                "underline": True, "italic": False,
            },
            "image": {
                "alignment": "center",
                "caption_font": "宋体", "caption_size": 9,
                "caption_color": "#666666",
            },
            "header": {
                "text": "", "font": "宋体", "size": 9,
                "color": "#666666", "alignment": "center",
            },
            "footer": {
                "text": "", "font": "宋体", "size": 9,
                "color": "#666666", "alignment": "center",
                "page_number": True,
            },
        },
        "page": {
            "margin_top": 2.54, "margin_bottom": 2.54,
            "margin_left": 3.18, "margin_right": 3.18,
            "paper_size": "A4", "orientation": "portrait",
            "columns": 1,
            "page_border_color": "", "page_border_width": 1.0,
            "background_color": "",
        },
        "footnotes": {
            "font": "宋体", "size": 9, "color": "#333333",
        },
        "endnotes": {
            "font": "宋体", "size": 9, "color": "#333333",
        },
    }

    if "styles" in config:
        for key, value in config["styles"].items():
            if key in defaults["styles"] and isinstance(value, dict):
                defaults["styles"][key].update(value)

    if "page" in config:
        defaults["page"].update(config["page"])

    if "footnotes" in config and isinstance(config["footnotes"], dict):
        defaults["footnotes"].update(config["footnotes"])

    if "endnotes" in config and isinstance(config["endnotes"], dict):
        defaults["endnotes"].update(config["endnotes"])

    if "pandoc_extra_args" in config and isinstance(config["pandoc_extra_args"], list):
        defaults["pandoc_extra_args"] = config["pandoc_extra_args"]
    else:
        defaults["pandoc_extra_args"] = []

    return defaults


def analyze_and_generate_layout(
    client: APIClient,
    markdown_content: str,
    title: str,
    theme: str,
    remark: str = "",
    stop_event=None,
) -> dict:
    """
    分析 Markdown 文档内容结构，生成排版配置

    Args:
        client: API 客户端
        markdown_content: Markdown 格式的文档内容
        title: 文档标题
        theme: 主题
        remark: 备注/额外要求（同时适用于 AI 排版分析）
        stop_event: 停止事件

    Returns:
        排版配置字典
    """
    structure = _analyze_structure(markdown_content)

    prompt = _build_layout_prompt(title, theme, remark, structure, markdown_content)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位专业的文档排版设计师。请分析文档内容结构，"
                "并为其设计合适的排版方案。"
                "输出严格的 JSON 格式配置，包含三部分："
                "1. styles：用于生成 Word reference-doc 模板（主排版逻辑）；"
                "2. page + footnotes + endnotes：页面与注释配置；"
                "3. pandoc_extra_args：pandoc 转换引擎的额外参数列表。\n\n"
                "【可配置的样式属性说明】\n\n"
                "每个样式（styles 下的每个对象）可使用以下属性：\n\n"
                "字体属性:\n"
                "  font / name          字体名 (如 宋体, 黑体, Consolas)\n"
                "  size                 字号 (磅)\n"
                "  color                颜色 (#RRGGBB)\n"
                "  bold                 加粗 (true/false)\n"
                "  italic               斜体 (true/false)\n"
                "  strike               删除线 (true/false)\n"
                "  underline            下划线 (true/false)\n"
                "  superscript          上标 (true/false)\n"
                "  subscript            下标 (true/false)\n"
                "  character_spacing    字符间距 (磅，0 为标准)\n"
                "  shadow               阴影 (true/false)\n"
                "  outline              空心 (true/false)\n"
                "  emboss               浮雕 (true/false)\n"
                "  imprint              雕刻 (true/false)\n"
                "  glow                 发光 (true/false)\n\n"
                "段落属性:\n"
                "  alignment            对齐 (left/center/right/justify)\n"
                "  space_before         段前间距 (磅)\n"
                "  space_after          段后间距 (磅)\n"
                "  line_spacing         行距 (倍数，如 1.5)\n"
                "  first_line_indent    首行缩进 (磅)\n"
                "  left_indent          左缩进 (磅)\n"
                "  right_indent         右缩进 (磅)\n"
                "  tab_stops            制表位列表 (如 [{position: 720, alignment: 'left'}])\n"
                "  page_break_before    段前分页 (true/false)\n"
                "  page_break_after     段后分页 (true/false)\n\n"
                "表格专用属性 (table):\n"
                "  border               是否显示边框 (true/false)\n"
                "  border_color         边框颜色 (#RRGGBB)\n"
                "  border_width         边框宽度 (磅)\n"
                "  row_height           行高 (厘米)\n"
                "  cell_margin_top      单元格上内边距 (厘米)\n"
                "  cell_margin_bottom   单元格下内边距 (厘米)\n"
                "  cell_margin_left     单元格左内边距 (厘米)\n"
                "  cell_margin_right    单元格右内边距 (厘米)\n"
                "  cell_shading         单元格着色 (#RRGGBB，空字符串不启用)\n\n"
                "代码专用属性 (code/code块):\n"
                "  background_color     背景色 (#RRGGBB)\n\n"
                "行内代码属性 (inline_code):\n"
                "  font/size/color      字体/字号/颜色\n"
                "  background_color     背景色 (#RRGGBB)\n\n"
                "分割线属性 (hr):\n"
                "  color                线条颜色 (#RRGGBB)\n"
                "  width                线条宽度 (磅)\n"
                "  space_before/after   段前/段后间距 (磅)\n\n"
                "任务列表属性 (task_list):\n"
                "  font/size/color      字体/字号/颜色\n"
                "  line_spacing         行距\n"
                "  space_before/after   段前/段后间距 (磅)\n\n"
                "嵌套列表属性 (nested_list):\n"
                "  level2/level3         第二/三层级样式，包含 font/size/color/line_spacing/left_indent\n\n"
                "定义列表属性 (definition):\n"
                "  term_font/size/color 术语字体/字号/颜色\n"
                "  term_bold            术语加粗 (true/false)\n"
                "  definition_font/size/color 定义字体/字号/颜色\n"
                "  definition_italic    定义斜体 (true/false)\n"
                "  left_indent          左缩进 (磅)\n\n"
                "图片专用属性 (image):\n"
                "  alignment            对齐 (left/center/right)\n"
                "  caption_font/size/color  图注样式\n\n"
                "页眉页脚属性 (header/footer):\n"
                "  text                 页眉/页脚文本 (留空则不生成)\n"
                "  page_number          是否显示页码 (true/false，仅 footer)\n\n"
                "页面属性 (page):\n"
                "  paper_size           纸张大小 (A4/A3/A5/Letter/Legal)\n"
                "  orientation          页面方向 (portrait/landscape)\n"
                "  columns              分栏数 (1, 2, 3...)\n"
                "  page_border_color    页面边框颜色 (#RRGGBB，空字符串不启用)\n"
                "  page_border_width    页面边框宽度 (磅)\n"
                "  background_color     页面背景色 (#RRGGBB，空字符串不启用)\n\n"
                "【pandoc_extra_args 可选参数参考】\n"
                "  --toc / --toc-depth=N       目录生成\n"
                "  --number-sections           章节自动编号\n"
                "  --highlight-style=style     代码高亮\n"
                "  --color-links               链接着色\n"
                "  --citeproc / --bibliography 引用处理\n"
                "  --filter / --lua-filter     过滤器\n"
                "如无特殊需求，pandoc_extra_args 输出空列表 []。\n\n"
                "注意：仅在需要时配置对应属性，不需要的属性可省略（使用默认值）。"
                "字体、字号、颜色等样式在 styles 中配置，pandoc_extra_args 仅用于目录、编号、高亮等模板难以实现的功能。"
            ),
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat_completion(
            messages, temperature=0.7, max_tokens=4096, stop_event=stop_event
        )
        config = _extract_json(response)
        return _normalize_config(config)
    except (APIError, ValueError) as e:
        raise
    except Exception as e:
        raise ValueError(f"AI 排版分析失败: {str(e)}")


def _analyze_structure(markdown: str) -> dict:
    """分析 Markdown 文档的结构"""
    structure = {
        "has_title": False,
        "has_h1": False,
        "has_h2": False,
        "has_h3": False,
        "has_h4": False,
        "has_h5": False,
        "has_h6": False,
        "has_list": False,
        "has_table": False,
        "has_quote": False,
        "has_code": False,
        "has_inline_code": False,
        "has_bold": False,
        "has_image": False,
        "has_italic": False,
        "has_strike": False,
        "has_link": False,
        "has_footnote": False,
        "has_hr": False,
        "has_task_list": False,
        "has_definition": False,
        "content_length": len(markdown),
    }

    if re.search(r'^#\s', markdown, re.MULTILINE):
        structure["has_h1"] = True
        structure["has_title"] = True
    if re.search(r'^##\s', markdown, re.MULTILINE):
        structure["has_h2"] = True
    if re.search(r'^###\s', markdown, re.MULTILINE):
        structure["has_h3"] = True
    if re.search(r'^####\s', markdown, re.MULTILINE):
        structure["has_h4"] = True
    if re.search(r'^#####\s', markdown, re.MULTILINE):
        structure["has_h5"] = True
    if re.search(r'^######\s', markdown, re.MULTILINE):
        structure["has_h6"] = True
    if re.search(r'^[-*+]\s', markdown, re.MULTILINE):
        structure["has_list"] = True
    if re.search(r'\|.*\|', markdown):
        structure["has_table"] = True
    if re.search(r'^>\s', markdown, re.MULTILINE):
        structure["has_quote"] = True
    if re.search(r'```[\s\S]*```', markdown):
        structure["has_code"] = True
    if re.search(r'\*\*[^*]+\*\*', markdown):
        structure["has_bold"] = True
    if re.search(r'!\[.*\]\(.*\)', markdown):
        structure["has_image"] = True
    if re.search(r'\*[^*]+\*', markdown):
        structure["has_italic"] = True
    if re.search(r'~~[^~]+~~', markdown):
        structure["has_strike"] = True
    if re.search(r'\[.*\]\(.*\)', markdown):
        structure["has_link"] = True
    if re.search(r'\[\^.*\]', markdown):
        structure["has_footnote"] = True
    if re.search(r'`[^`]+`', markdown):
        structure["has_inline_code"] = True
    if re.search(r'^\s*---\s*$', markdown, re.MULTILINE):
        structure["has_hr"] = True
    if re.search(r'^\s*[-*+]\s+\[[ xX]\]', markdown, re.MULTILINE):
        structure["has_task_list"] = True
    if re.search(r'^:\s', markdown, re.MULTILINE):
        structure["has_definition"] = True

    return structure


def _build_layout_prompt(
    title: str, theme: str, remark: str, structure: dict, markdown: str
) -> str:
    """构建排版分析的 prompt"""
    remark_text = remark if remark.strip() else "无"

    structure_desc = []
    if structure["has_title"]:
        structure_desc.append("包含主标题")
    if structure["has_h1"]:
        structure_desc.append("包含一级标题")
    if structure["has_h2"]:
        structure_desc.append("包含二级标题")
    if structure["has_h3"]:
        structure_desc.append("包含三级标题")
    if structure["has_h4"]:
        structure_desc.append("包含四级标题")
    if structure["has_h5"]:
        structure_desc.append("包含五级标题")
    if structure["has_h6"]:
        structure_desc.append("包含六级标题")
    if structure["has_list"]:
        structure_desc.append("包含列表")
    if structure["has_table"]:
        structure_desc.append("包含表格")
    if structure["has_quote"]:
        structure_desc.append("包含引用")
    if structure["has_code"]:
        structure_desc.append("包含代码块")
    if structure["has_bold"]:
        structure_desc.append("包含加粗文本")
    if structure["has_italic"]:
        structure_desc.append("包含斜体文本")
    if structure["has_strike"]:
        structure_desc.append("包含删除线文本")
    if structure["has_image"]:
        structure_desc.append("包含图片")
    if structure["has_link"]:
        structure_desc.append("包含超链接")
    if structure["has_footnote"]:
        structure_desc.append("包含脚注")
    if structure["has_inline_code"]:
        structure_desc.append("包含行内代码")
    if structure["has_hr"]:
        structure_desc.append("包含分割线")
    if structure["has_task_list"]:
        structure_desc.append("包含任务列表")
    if structure["has_definition"]:
        structure_desc.append("包含定义列表")

    content_preview = markdown[:500] if len(markdown) > 500 else markdown

    prompt = f"""请为以下文档设计最合适的排版方案。

文档标题: {title}
主题: {theme}
文档结构: {', '.join(structure_desc) if structure_desc else '结构简单'}
内容长度: 约 {structure['content_length']} 字符

文档预览:
```markdown
{content_preview}
```

用户额外要求（同时适用于排版）: {remark_text}

请根据文档的内容类型和结构特点，设计合适的排版方案。
请考虑：
1. 文档类型（报告/散文/技术文档/论文/简报等）
2. 标题层级的视觉层次
3. 正文字体大小和行距的可读性
4. 颜色搭配的专业性和美观性
5. 页边距与纸张大小的合理性
6. 是否需要目录、章节编号、代码高亮等特殊功能
7. 代码块是否需要独立样式和背景色
8. 表格是否需要边框、行高、单元格间距
9. 是否需要页眉页脚和页码
10. 是否需要多栏布局

请输出严格的 JSON 格式配置。以下是完整的属性列表（仅输出需要覆盖的属性，其他可省略）：

{{
  "styles": {{
    "default_font": {{"name": "宋体", "size": 11, "color": "#000000"}},
    "title": {{"font": "黑体", "size": 22, "color": "#1a1a1a", "bold": true, "alignment": "center", "space_before": 24, "space_after": 18}},
    "h1": {{"font": "黑体", "size": 18, "color": "#1a365d", "bold": true, "space_before": 24, "space_after": 12}},
    "h2": {{"font": "黑体", "size": 15, "color": "#2c5282", "bold": true, "space_before": 20, "space_after": 10}},
    "h3": {{"font": "黑体", "size": 13, "color": "#2b6cb0", "bold": true, "space_before": 16, "space_after": 8}},
    "h4": {{"font": "黑体", "size": 12, "color": "#3182ce", "bold": true, "space_before": 14, "space_after": 6}},
    "h5": {{"font": "黑体", "size": 11, "color": "#4299e1", "bold": true, "space_before": 12, "space_after": 6}},
    "h6": {{"font": "黑体", "size": 10.5, "color": "#63b3ed", "bold": true, "space_before": 10, "space_after": 4}},
    "body": {{"font": "宋体", "size": 11, "color": "#000000", "line_spacing": 1.5, "first_line_indent": 22}},
    "quote": {{"font": "楷体", "size": 11, "color": "#4a5568", "left_indent": 44, "right_indent": 44}},
    "list": {{"font": "宋体", "size": 11, "color": "#000000", "line_spacing": 1.4}},
    "nested_list": {{"level2": {{"font": "宋体", "size": 10.5, "color": "#333333", "line_spacing": 1.3, "left_indent": 22}}}}}},
    "code": {{"font": "Consolas", "size": 10, "color": "#2d3748", "background_color": "#f7fafc", "left_indent": 20}},
    "inline_code": {{"font": "Consolas", "size": 10, "color": "#2d3748", "background_color": "#f0f0f0"}},
    "hr": {{"color": "#999999", "width": 1.0, "space_before": 12, "space_after": 12}},
    "task_list": {{"font": "宋体", "size": 11, "color": "#000000", "line_spacing": 1.4}},
    "definition": {{"term_font": "黑体", "term_size": 11, "term_color": "#1a202c", "term_bold": true, "definition_font": "宋体", "definition_size": 11, "definition_color": "#000000", "left_indent": 44}},
    "table": {{"font": "宋体", "size": 10, "color": "#000000", "border": true, "border_color": "#000000", "border_width": 0.5, "row_height": 0.8, "cell_margin_top": 0.1, "cell_margin_bottom": 0.1, "cell_margin_left": 0.1, "cell_margin_right": 0.1, "cell_shading": ""}},
    "link": {{"font": "宋体", "size": 11, "color": "#3182ce", "underline": true}},
    "image": {{"alignment": "center", "caption_font": "宋体", "caption_size": 9, "caption_color": "#666666"}},
    "header": {{"text": "", "font": "宋体", "size": 9, "color": "#666666", "alignment": "center"}},
    "footer": {{"text": "", "font": "宋体", "size": 9, "color": "#666666", "alignment": "center", "page_number": true}}
  }},
  "page": {{
    "margin_top": 2.54, "margin_bottom": 2.54,
    "margin_left": 3.18, "margin_right": 3.18,
    "paper_size": "A4", "orientation": "portrait",
    "columns": 1,
    "page_border_color": "", "page_border_width": 1.0,
    "background_color": ""
  }},
  "footnotes": {{"font": "宋体", "size": 9, "color": "#333333"}},
  "endnotes": {{"font": "宋体", "size": 9, "color": "#333333"}},
  "pandoc_extra_args": []
}}

各属性说明：
- font/size/color: 字体名/字号(磅)/颜色(#RRGGBB)
- bold/italic/strike/underline: 加粗/斜体/删除线/下划线 (true/false)
- superscript/subscript: 上标/下标 (true/false)
- character_spacing: 字符间距 (磅)
- shadow/outline/emboss/imprint/glow: 阴影/空心/浮雕/雕刻/发光 (true/false)
- alignment: left/center/right/justify
- space_before/space_after: 段前/段后间距 (磅)
- line_spacing: 行距 (倍数)
- first_line_indent/left_indent/right_indent: 缩进 (磅)
- tab_stops: 制表位列表，如 [{{"position": 720, "alignment": "left"}}]
- page_break_before/page_break_after: 段前/段后分页 (true/false)
- border/border_color/border_width: 边框开关/颜色/宽度
- row_height: 表格行高 (厘米)
- cell_margin_*: 单元格内边距 (厘米)
- cell_shading: 单元格底纹颜色 (#RRGGBB，空字符串不启用)
- background_color: 代码块/页面背景色
- page_border_color/page_border_width: 页面边框颜色(#RRGGBB)/宽度(磅)
- paper_size: A4/A3/A5/Letter/Legal
- orientation: portrait(纵向)/landscape(横向)
- columns: 分栏数
- page_number: 显示页码 (true/false)
- pandoc_extra_args: pandoc 参数列表，如 ["--toc", "--number-sections"]

注意：
- 仅输出 JSON，不要添加任何解释或额外文本
- 不需要覆盖的属性可省略，会自动使用默认值
- 特殊控制功能（目录、编号、高亮等）通过 pandoc_extra_args 实现"""

    return prompt