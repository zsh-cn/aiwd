"""Prompt 模板集中管理"""

TITLE_GENERATION_PROMPT = """你是一位专业内容创作者。请围绕主题"{theme}"，生成{count}个文章标题。
要求：标题简洁有吸引力，不重复，覆盖不同子角度。
额外要求：{remark}
请仅输出标题列表，每行一个，不要编号。"""

DOC_GENERATION_PROMPT = """请以"{title}"为标题，围绕主题"{theme}"，撰写一篇完整的文章。
要求：
- 使用 Markdown 格式输出
- 包含适当的小标题、段落和列表
- 内容充实，逻辑清晰
额外要求：{remark}
直接输出 Markdown 内容，不要额外解释。"""


def build_title_prompt(theme: str, count: int, remark: str = "") -> str:
    remark_text = remark if remark.strip() else "无"
    return TITLE_GENERATION_PROMPT.format(theme=theme, count=count, remark=remark_text)


def build_doc_prompt(theme: str, title: str, remark: str = "", word_count: int = 0) -> str:
    remark_text = remark if remark.strip() else "无"
    prompt = DOC_GENERATION_PROMPT.format(theme=theme, title=title, remark=remark_text)
    if word_count > 0:
        prompt += f"\n\n文章字数要求：约 {word_count} 字左右。"
    return prompt