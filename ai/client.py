"""AI请求模块 —— 适配所有 OpenAI 兼容 API"""

import openai


class AIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, base_url: str, api_key: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._client = openai.OpenAI(base_url=self._base_url, api_key=self._api_key)

    def test_connection(self) -> bool:
        """测试连接是否正常，正常返回 True，否则抛出异常"""
        try:
            self._client.models.list()
            return True
        except openai.AuthenticationError:
            raise ConnectionError("API Key 无效或认证失败")
        except openai.APIConnectionError:
            raise ConnectionError(f"无法连接到 {self._base_url}，请检查 Base URL 和网络")
        except openai.APIStatusError as e:
            raise ConnectionError(f"接口返回错误 (HTTP {e.status_code}): {e.message}")
        except Exception as e:
            raise ConnectionError(f"连接测试失败: {e}")

    def chat(self, messages: list, temperature: float = 0.8) -> str:
        """发送聊天请求并返回回复文本"""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except openai.APIError as e:
            raise RuntimeError(f"AI 接口请求失败: {e}")

    def generate_titles(self, topic: str, file_count: int, word_count: int) -> list[str]:
        """根据主题、文件数量、目标字数生成标题列表"""
        system_prompt = (
            "你是一个专业的文章标题生成助手。请根据用户提供的主题，生成指定数量的文章标题。"
            "每个标题对应一篇约{word_count}字的文章篇幅。标题应具有吸引力、层次分明、覆盖主题的不同角度。"
            "请严格按照以下格式输出，每行一个标题，不要编号，不要多余内容：\n"
            "标题1\n标题2\n..."
        ).format(word_count=word_count)

        user_prompt = (
            "主题：{topic}\n"
            "需要生成 {count} 个文章标题，每篇文章约 {word_count} 字。"
        ).format(topic=topic, count=file_count, word_count=word_count)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = self.chat(messages, temperature=0.9)
        titles = [line.strip() for line in result.strip().split("\n") if line.strip()]
        titles = [t.lstrip("0123456789.、-）) ").strip() for t in titles]
        return titles[:file_count]

    def generate_content(self, title: str, word_count: int) -> str:
        """根据标题和目标字数生成文章正文"""
        system_prompt = (
            "你是一个专业的内容创作助手。请根据用户提供的标题，撰写一篇完整的文章正文。"
            "文章必须严格控制在约 {word_count} 字（中文字符数）左右，偏差不超过 ±5%。"
            "请直接输出文章正文，不要包含标题、署名、声明等额外内容。"
        ).format(word_count=word_count)

        user_prompt = (
            "请撰写以下标题的文章正文：\n"
            "《{title}》\n\n"
            "要求：字数严格控制在约 {word_count} 字。"
        ).format(title=title, word_count=word_count)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.chat(messages, temperature=0.8)