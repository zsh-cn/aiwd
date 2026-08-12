"""字数参数处理模块"""


class WordCountHandler:
    """字数参数校验与处理"""

    @staticmethod
    def validate(value) -> int:
        """校验字数是否为合法正整数，合法则返回 int，否则抛出 ValueError"""
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("字数不能为空")
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"字数必须为整数，当前值: {value}")
        if num <= 0:
            raise ValueError(f"字数必须为正整数，当前值: {num}")
        return num

    @staticmethod
    def clamp(value: int, min_val: int = 50, max_val: int = 50000) -> int:
        """将字数限制在合理范围内"""
        if value < min_val:
            return min_val
        if value > max_val:
            return max_val
        return value

    @staticmethod
    def count_chinese_chars(text: str) -> int:
        """统计中文字符数（含中文标点，不含英文和数字）"""
        count = 0
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
                count += 1
        return count

    @staticmethod
    def estimate_total_chars(text: str) -> int:
        """估算文本总字符数（所有非空白字符）"""
        return sum(1 for ch in text if not ch.isspace())