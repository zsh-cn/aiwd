import re

from api_client import APIClient
from utils.prompt_templates import build_title_prompt


class TitleGenerator:

    def __init__(self, client: APIClient):
        self.client = client

    def generate_titles(
        self,
        theme: str,
        count: int,
        remark: str = "",
        progress_callback=None,
        status_callback=None,
        item_callback=None,
        stop_event=None,
    ) -> list:
        prompt = build_title_prompt(theme, count, remark)
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的内容策划，擅长生成有吸引力的文章标题。",
            },
            {"role": "user", "content": prompt},
        ]

        if status_callback:
            status_callback("正在生成标题列表...")

        titles = []
        buffer = ""
        full_text = ""

        for chunk in self.client.chat_completion_stream(messages, temperature=0.9, stop_event=stop_event):
            if stop_event and stop_event.is_set():
                break

            full_text += chunk
            buffer += chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                line = re.sub(r'^\d+[\.、\-•·]\s*', '', line)
                if line:
                    titles.append(line)
                    if item_callback:
                        item_callback(line)
                    if progress_callback:
                        progress_callback(min(len(titles), count), count)
                    if status_callback:
                        status_callback(f"已生成 {len(titles)}/{count} 个标题")

        if buffer.strip() and not (stop_event and stop_event.is_set()):
            line = buffer.strip()
            line = re.sub(r'^\d+[\.、\-•·]\s*', '', line)
            if line:
                titles.append(line)
                if item_callback:
                    item_callback(line)
                if progress_callback:
                    progress_callback(min(len(titles), count), count)

        return titles[:count]