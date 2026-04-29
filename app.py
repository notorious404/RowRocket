# table_extractor_app.py
import os
from typing import List, Dict, Any

import streamlit as st

from pdf_doc_loader import save_and_read_uploaded_files
from pdf_table_extractor import TableExtractor
from table_pdf_report import TableReportGenerator
from utils import ensure_directories, build_report_name

def main():
    st.set_page_config(page_title="Table Extractor", layout="wide")
    st.title("Table Extractor")

    st.write(
        "Upload one or more PDF / DOCX files. "
        "The app will extract tables (including pipe tables) and generate a single consolidated PDF report."
    )

    uploaded_files = st.file_uploader(
        "Upload PDF / DOCX files",
        type=["pdf", "docx", "doc"],
        accept_multiple_files=True,
    )

    run_button = st.button("Extract tables")

    if run_button:
        if not uploaded_files:
            st.warning("Please upload at least one file.")
            return

        ensure_directories()

        progress_text = "Starting table extraction..."
        progress_bar = st.progress(0, text=progress_text)

        # Step 1: Save and read files
        progress_bar.progress(5, text="Saving and reading uploaded files...")
        file_texts = save_and_read_uploaded_files(uploaded_files)

        progress_bar.progress(20, text="Initializing ChatGPT table extractor...")
        extractor = TableExtractor()

        all_tables: List[Dict[str, Any]] = []
        total_files = len(file_texts)
        processed = 0

        # Step 2: Extract tables per file
        for path, text in file_texts.items():
            processed += 1
            fname = os.path.basename(path)
            step_msg = f"Extracting tables from {fname} ({processed}/{total_files})..."
            base_progress = 20 + int(60 * (processed - 1) / max(total_files, 1))
            progress_bar.progress(base_progress, text=step_msg)

            if not text.strip():
                continue

            tables = extractor.extract_tables_from_text(fname, text)
            all_tables.extend(tables)

            current_progress = 20 + int(60 * (processed) / max(total_files, 1))
            progress_bar.progress(current_progress, text=step_msg)

        # Step 3: Generate report
        pdf_names = [uf.name for uf in uploaded_files]
        report_path = build_report_name(pdf_names, suffix="TABLES")

        progress_bar.progress(90, text="Generating consolidated tables PDF report...")
        report_generator = TableReportGenerator(output_path=report_path)
        report_generator.build(all_tables)

        progress_bar.progress(100, text="Done.")
        progress_bar.empty()

        st.success("Table extraction complete. Download your report below.")
        with open(report_path, "rb") as f:
            st.download_button(
                label="⬇️ Download tables report",
                data=f,
                file_name=os.path.basename(report_path),
                mime="application/pdf",
                use_container_width=True,
            )

        st.write(f"Report saved at: `{report_path}`")

if __name__ == "__main__":
    main()
