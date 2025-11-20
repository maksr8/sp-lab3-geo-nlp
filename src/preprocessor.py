import re


class TextPreprocessor:
    def clean(self, text: str) -> str:
        text = re.sub(r'^\d+[\.\°\•]*\s*', '', text)
        text = re.sub(r'\(рис\.\s*\d+\)', '', text)
        text = text.replace("—", "-").replace("`", "'").replace("’", "'")
        text = text.replace("∠", " кут ").replace("°", "")
        text = re.sub(r'\b(відповідно|зображених на|даного)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?<=[^\d])\.(?=[^\d])', ' . ', text)
        text = text.replace(",", " , ")

        return text.strip()