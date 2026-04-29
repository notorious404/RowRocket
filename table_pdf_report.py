# table_pdf_report.py
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class TableReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.story = []

    def _add_title(self, title: str):
        style = self.styles["Heading1"]
        self.story.append(Paragraph(title, style))
        self.story.append(Spacer(1, 12))

    def _add_subtitle(self, text: str):
        style = self.styles["Heading3"]
        self.story.append(Paragraph(text, style))
        self.story.append(Spacer(1, 6))

    def _add_table(self, table_info: Dict[str, Any]):
        headers = table_info.get("headers", [])
        rows = table_info.get("rows", [])
        source = table_info.get("source_file", "")
        title = table_info.get("title", "")
        idx = table_info.get("index", 1)

        caption_text = f"Table {idx} from {source}"
        if title:
            caption_text += f" – {title}"
        caption_style = ParagraphStyle(
            "Caption",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=12,
            spaceAfter=4,
        )
        self.story.append(Paragraph(caption_text, caption_style))

        data = []
        if headers:
            data.append(headers)
        data.extend(rows)

        # Wrap text in Paragraphs for automatic wrapping.
        wrapped_data = []
        normal_style = self.styles["Normal"]
        for row in data:
            wrapped_row = [Paragraph(str(cell), normal_style) for cell in row]
            wrapped_data.append(wrapped_row)

        # Simple fixed widths: adjust as needed.
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 1)
        if num_cols <= 4:
            col_widths = [120] * num_cols
        else:
            # Try to fit into page width for many columns
            total_width = 500
            col_widths = [total_width / num_cols] * num_cols

        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("WORDWRAP", (0, 0), (-1, -1), True),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        self.story.append(table)
        self.story.append(Spacer(1, 18))

    def build(self, all_tables: List[Dict[str, Any]]):
        doc = SimpleDocTemplate(self.output_path, pagesize=A4)
        self._add_title("Consolidated Tables Report")

        if not all_tables:
            self._add_subtitle("No tables were detected in the uploaded documents.")
        else:
            current_file = None
            for t in all_tables:
                if t.get("source_file") != current_file:
                    current_file = t.get("source_file")
                    self._add_subtitle(f"Source: {current_file}")
                self._add_table(t)

        doc.build(self.story)
