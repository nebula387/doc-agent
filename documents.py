import io
import fitz        # pymupdf
import docx        # python-docx

# { user_id: { filename: {"name": str, "text": str} } }
user_documents: dict = {}

MAX_DOC_CHARS = 40_000
MAX_DOCS = 5

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc).strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("cp1251", errors="ignore").strip()

def save_document(user_id: int, filename: str, file_bytes: bytes) -> str:
    filename_lower = filename.lower()
    try:
        if filename_lower.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        elif filename_lower.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
        elif filename_lower.endswith(".txt"):
            text = extract_text_from_txt(file_bytes)
        else:
            return "❌ Поддерживаются форматы: PDF, DOCX, TXT"

        if not text:
            return "❌ Не удалось извлечь текст. Файл пустой или защищён."

        if user_id not in user_documents:
            user_documents[user_id] = {}

        docs = user_documents[user_id]

        if filename not in docs and len(docs) >= MAX_DOCS:
            return f"❌ Максимум {MAX_DOCS} документов. Удали один через /deldoc или все через /cleardocs"

        truncated = len(text) > MAX_DOC_CHARS
        if truncated:
            text = text[:MAX_DOC_CHARS]

        docs[filename] = {"name": filename, "text": text}

        msg = (
            f"✅ <b>{filename}</b> загружен ({len(text):,} символов).\n"
            f"Документов: {len(docs)}/{MAX_DOCS}"
        )
        if truncated:
            msg += "\n⚠️ Документ большой — загружена первая часть."
        return msg

    except Exception as e:
        return f"❌ Ошибка при обработке файла: {e}"

def get_combined_text(user_id: int) -> str | None:
    docs = user_documents.get(user_id, {})
    if not docs:
        return None
    parts = []
    for filename, doc in docs.items():
        parts.append(f"=== Документ: {filename} ===\n{doc['text']}")
    return "\n\n".join(parts)

def get_documents(user_id: int) -> dict:
    return user_documents.get(user_id, {})

def remove_document(user_id: int, filename: str) -> str:
    docs = user_documents.get(user_id, {})
    if filename in docs:
        del docs[filename]
        if not docs:
            user_documents.pop(user_id, None)
        return f"🗑 <b>{filename}</b> удалён."
    return f"❌ Документ <b>{filename}</b> не найден."

def clear_documents(user_id: int):
    user_documents.pop(user_id, None)

def list_documents(user_id: int) -> str:
    docs = user_documents.get(user_id, {})
    if not docs:
        return "📭 Документов нет. Отправь PDF, DOCX или TXT."
    lines = [f"📂 <b>Документы ({len(docs)}/{MAX_DOCS}):</b>\n"]
    for i, (filename, doc) in enumerate(docs.items(), 1):
        lines.append(f"{i}. {filename} — {len(doc['text']):,} симв.")
    lines.append("\n/deldoc <i>имя файла</i> — удалить")
    lines.append("/cleardocs — удалить все")
    return "\n".join(lines)
