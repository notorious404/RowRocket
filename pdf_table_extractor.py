# pdf_table_extractor.py
import json
from typing import List, Dict, Any
from openai import OpenAI

from config import MODEL_NAME, MAX_TOKENS, TEMPERATURE

client = OpenAI()

class TableExtractor:
    def __init__(self, model_name: str = MODEL_NAME,
                 temperature: float = TEMPERATURE,
                 max_tokens: int = MAX_TOKENS):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _build_prompt(self, file_name: str, text: str) -> str:
        return f"""
You are a table extraction engine.

Input comes from a document: {file_name}.
The text may contain:
- visually formatted tables
- markdown-style pipe tables, for example:
  | Col1 | Col2 |
  | ---- | ---- |
  | A    | B    |
- messy or partial tables split across lines.

Your task:
1. Find ALL tables in the text, including pipe tables.
2. Reconstruct each table as clean structured data.
3. Return ONLY valid JSON in this exact format:

{{
  "tables": [
    {{
      "source_file": "<original file name>",
      "title": "<short title or description, or empty string>",
      "index": 1,
      "headers": ["col1", "col2", ...],
      "rows": [
        ["r1c1", "r1c2", ...],
        ["r2c1", "r2c2", ...]
      ]
    }},
    ...
  ]
}}

Rules:
- Always return a JSON object with a "tables" key.
- Each table must have the same number of items in every row as in "headers".
- If no tables are found, return {{"tables": []}}.
- Normalize pipe tables and other styles into rows and columns.
- Do not include any explanation, only JSON.
        """.strip()

    def extract_tables_from_text(self, file_name: str, text: str) -> List[Dict[str, Any]]:
        prompt = self._build_prompt(file_name, text)

        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt + "\n\n" + text}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        content = response.choices[0].message.content.strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to salvage by trimming to JSON substring if needed
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(content[start:end+1])
                except Exception:
                    data = {"tables": []}
            else:
                data = {"tables": []}

        tables = data.get("tables", [])
        # ensure minimal structure
        normalized = []
        for idx, t in enumerate(tables, start=1):
            headers = t.get("headers") or []
            rows = t.get("rows") or []
            title = t.get("title") or ""
            normalized.append(
                {
                    "source_file": t.get("source_file") or file_name,
                    "title": title,
                    "index": t.get("index") or idx,
                    "headers": headers,
                    "rows": rows,
                }
            )
        return normalized
