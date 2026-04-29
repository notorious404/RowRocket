# ⬡ RowRocket — AI-Powered Table Extraction

> **Extract Tables. Instantly.**
> Upload any PDF or document — get clean, structured table data in seconds. No manual copy-paste. Ever again.

## ✦ What is RowRocket?

**RowRocket** automatically detects, extracts, and reconstructs tables from **PDF and DOCX files** — including scanned documents using OCR. It supports multi-page files, complex layouts, and AI-powered table reconstruction, delivering results as a clean, consolidated PDF report.

---

## 🚀 Features

- 📤 **Upload PDF and DOCX files** — drag & drop or browse
- 🧠 **Smart Detection** — works on both digital and scanned documents
- 🔍 **OCR Support** — Tesseract-powered extraction for scanned PDFs
- 📊 **Accurate Reconstruction** — preserves table structure, even complex and pipe-based formats
- 🤖 **AI-Powered** — OpenAI intelligently reconstructs ambiguous tables
- 📄 **PDF Report Generation** — consolidated output of all extracted tables
- 📈 **Real-Time Progress Tracking** — live feedback during extraction
- 🗂️ **Multi-Page Support** — handles large, multi-page documents seamlessly

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| UI | Streamlit |
| PDF Extraction | pdfplumber |
| OCR Engine | Tesseract OCR |
| AI Reconstruction | OpenAI API |
| Report Generation | ReportLab |

---

## 📂 How It Works

```
01 Upload    →   Drop your PDF or DOCX into the upload zone
02 Extract   →   AI detects and parses every table automatically
03 Export    →   Download as PDF report or CSV — ready to use
```

1. Upload a **PDF or DOCX** file
2. RowRocket detects whether the document is **digital or scanned**
3. **OCR is applied** if required (Tesseract)
4. Table structures are **identified and parsed**
5. OpenAI **reconstructs** complex or ambiguous tables
6. A **consolidated PDF report** is generated with all extracted tables

---

## 📌 Use Cases

- 📊 Financial and audit reports
- 📚 Research papers and academic documents
- 🏛️ Government and legal PDFs
- 🧾 Invoices and statements
- 📋 Any document containing structured tables

---

## ⚙️ Installation

```bash
git clone https://github.com/notorious404/TABLE-EXTRACTION-APP.git
cd TABLE-EXTRACTION-APP
pip install -r requirements.txt
```

### 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📄 Output

- ✅ Clean, structured tables extracted from any document
- ✅ Consolidated PDF report containing all extracted tables
- ✅ Readable and analysis-ready format

---

## ⚡ Performance Notes

| Factor | Detail |
|---|---|
| Processing Speed | Results in seconds for most documents |
| OCR Accuracy | Depends on scan quality and resolution |
| Complex Tables | AI reconstruction handles most edge cases |
| Irregular Tables | Highly irregular formats may need manual review |

---

## 🧩 Scope

> ✅ This project focuses **only on table extraction**.
> 🔗 Comparison logic is handled in a [separate repository](https://github.com/notorious404).

---

## 🔒 Privacy & Security

Files are processed server-side and **never stored permanently**. Your documents stay private.

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🧑‍💻 Author

**Shantanu Yadav** — Frontend Developer

[![GitHub](https://img.shields.io/badge/GitHub-notorious404-181717?style=flat-square&logo=github)](https://github.com/notorious404)

---

<div align="center">
  <strong>⬡ RowRocket</strong> — Built with ❤️ for developers
</div>
