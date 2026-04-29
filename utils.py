# utils.py
import os
from datetime import datetime

def ensure_directories():
    directories = ["input_pdfs", "output_reports", "temp"]
    for d in directories:
        os.makedirs(d, exist_ok=True)

def build_report_name(pdf_names, suffix: str = "TABLES") -> str:
    """
    pdf_names: list of original uploaded filenames.
    suffix: tag like TABLES or COMPARE, etc.
    Naming style kept same as your compare model: names joined with _VS_ and timestamp.
    """
    base_name = "_VS_".join(
        [os.path.splitext(os.path.basename(n))[0] for n in pdf_names]
    )
    # optional: keep length reasonable
    base_name = base_name[:120]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{suffix}_{timestamp} report.pdf"
    return os.path.join("output_reports", filename)
