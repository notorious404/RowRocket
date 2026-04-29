# import glob
# import os

# from pdf_table_reader import extract_tables_from_pdf, ocr_pages_from_pdf
# from docx_table_reader import extract_tables_from_docx
# from pdf_table_extractor import (
#     clean_tables_with_chatgpt,
#     extract_tables_from_ocr_text,
# )
# from report_generator import TablesReportGenerator
# from utils import ensure_directories, build_report_name

# def main():
#     ensure_directories()
#     files = glob.glob("input_docs/*.pdf") + glob.glob("input_docs/*.docx")
#     if not files:
#         print("Place PDF/DOCX files into input_docs/ and rerun.")
#         return

#     all_clean_tables = []

#     for path in files:
#         filename = os.path.basename(path)
#         ext = os.path.splitext(path)[1].lower()

#         if ext == ".pdf":
#             raw_tables = extract_tables_from_pdf(path)
#             ocr_pages = ocr_pages_from_pdf(path)
#             cleaned_structured = clean_tables_with_chatgpt(filename, raw_tables)
#             ocr_tables = extract_tables_from_ocr_text(filename, ocr_pages)
#             all_clean_tables.extend(cleaned_structured)
#             all_clean_tables.extend(ocr_tables)
#         else:
#             raw_tables = extract_tables_from_docx(path)
#             cleaned_structured = clean_tables_with_chatgpt(filename, raw_tables)
#             all_clean_tables.extend(cleaned_structured)

#     if not all_clean_tables:
#         print("No tables detected.")
#         return

#     report_name = build_report_name(files)
#     report_path = os.path.join("output_reports", report_name)
#     gen = TablesReportGenerator(report_path)
#     gen.build(all_clean_tables)
#     print(f"Report written to {report_path}")

# if __name__ == "__main__":
#     main()
