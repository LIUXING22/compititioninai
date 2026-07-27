"""
Document parser - handles old .doc (OLE2 binary), .pdf, and text chunking.
"""
import os
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    chunk_index: int
    metadata: Dict = field(default_factory=dict)
    parent_text: str = ""  # parent document block for context window (1500 chars)


# ── OLE2 .doc parsing ──────────────────────────────────────────────────

def _read_fib(wd: bytes):
    """Read File Information Block from WordDocument stream."""
    # FIB base is at offset 0, length varies
    # Byte 0x20-0x21: cbRgFcLcb (FIB length in bytes, little-endian)
    if len(wd) < 0x22:
        return 0
    return struct.unpack_from('<H', wd, 0x20)[0]


def _extract_text_from_doc(data: bytes) -> str:
    """Extract readable text from old .doc binary using olefile."""
    try:
        import olefile
    except ImportError:
        return ""

    # Write to temp file for olefile (it needs a file path)
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as f:
        f.write(data)
        tmp_path = f.name

    try:
        ole = olefile.OleFileIO(tmp_path)

        if not ole.exists('WordDocument'):
            ole.close()
            return ""

        wd = ole.openstream('WordDocument').read()
        fib_len = _read_fib(wd)

        # Text in old .doc is stored as ANSI (single-byte) or Unicode after FIB
        # For Chinese .doc, it's typically Unicode (UTF-16LE)
        # The text starts at offset determined by ccpText in FIB

        # Simplified approach: read WordDocument, look for text markers
        # For WPS-created .doc files, text follows FIB structure

        # Try Unicode extraction: scan for Chinese text blocks
        # The FIB tells us where text starts. In practice, for simple extraction
        # we scan the WordDocument for UTF-16LE Chinese characters

        all_text = []

        # Method 1: Extract from WordDocument stream (Unicode text region)
        # FIB is at start, text region starts after FIB and runs for ccpText * 2 bytes
        # We use a simpler method: find the first "一" or similar marker

        # The Chinese text "一" (U+4E00) in UTF-16LE is b'\x00\x4E'
        marker = b'\x00\x4e'
        text_start = wd.find(marker)

        if text_start >= 0:
            # Try to decode from this point as UTF-16LE
            raw_text = wd[text_start:]
            try:
                decoded = raw_text.decode('utf-16-le', errors='surrogatepass')
                # Clean up: keep only printable characters
                cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', decoded)
                # Remove surrogate/replacement chars
                cleaned = re.sub(r'[\ud800-\udfff�]', '', cleaned)
                if len(cleaned.strip()) > 50:
                    all_text.append(cleaned)
            except Exception:
                pass

        # Method 2: Also try reading ANSI text
        # In old .doc, text might be in ANSI portion. Try common Chinese encodings
        for encoding in ['gb18030', 'gb2312', 'gbk', 'utf-8']:
            try:
                decoded = wd[fib_len:fib_len+50000].decode(encoding, errors='replace')
                # Check if it has substantial Chinese content
                chinese_chars = len(re.findall(r'[一-鿿]', decoded))
                if chinese_chars > 100:
                    all_text.append(decoded)
                    break
            except Exception:
                continue

        ole.close()

        result = '\n'.join(all_text)

        # If still empty, try the Data stream
        if not result.strip() and ole.exists('Data'):
            try:
                ole2 = olefile.OleFileIO(tmp_path)
                data_stream = ole2.openstream('Data').read()
                for encoding in ['utf-16-le', 'gb18030', 'gb2312', 'utf-8']:
                    try:
                        decoded = data_stream.decode(encoding, errors='replace')
                        chinese_chars = len(re.findall(r'[一-鿿]', decoded))
                        if chinese_chars > 100:
                            result = decoded
                            break
                    except Exception:
                        continue
                ole2.close()
            except Exception:
                pass

        return result

    finally:
        os.unlink(tmp_path)


# ── PDF parsing ────────────────────────────────────────────────────────

def _extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF using PyMuPDF (lazy import)."""
    try:
        import fitz
    except ImportError:
        print(f"  WARNING: PyMuPDF not available for PDF parsing")
        return ""
    doc = fitz.open(filepath)
    all_text = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            all_text.append(text)
    doc.close()
    return '\n'.join(all_text)


# ── Text chunking ──────────────────────────────────────────────────────

def _split_into_sentences(text: str) -> List[str]:
    """Split Chinese text into sentences."""
    # Split on Chinese punctuation
    sentences = re.split(r'[\n\r]+|(?<=[。！？；\?\.!\n])', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
    source: str = "unknown",
    parent_window: int = 1000,
) -> List[DocumentChunk]:
    """Split text into overlapping chunks with parent context windows.

    Each chunk has:
    - text: small chunk for retrieval (chunk_size chars)
    - parent_text: larger window for LLM context (~chunk_size + 2*parent_window chars)
    """
    sentences = _split_into_sentences(text)

    chunks = []
    current_chunk = ""
    chunk_idx = 0
    chunk_id_base = Path(source).stem.replace(' ', '_').replace('.', '_')

    # Also keep the full sentence list for parent window construction
    all_sentences = sentences.copy()

    for i, sentence in enumerate(all_sentences):
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence
        else:
            if current_chunk.strip():
                # Build parent context: collect sentences around this chunk
                parent_start = max(0, i - len(current_chunk))
                parent_end = min(len(all_sentences), i + 10)
                parent_sentences = all_sentences[parent_start:parent_end]
                parent_text = ''.join(parent_sentences)

                # Trim parent_text to reasonable size (~chunk_size + 2*parent_window)
                center = len(parent_text) // 2
                half = chunk_size // 2 + parent_window
                if len(parent_text) > chunk_size + 2 * parent_window:
                    start = max(0, center - half)
                    end = min(len(parent_text), center + half)
                    parent_text = parent_text[start:end]

                chunks.append(DocumentChunk(
                    chunk_id=f"{chunk_id_base}-chunk-{chunk_idx:04d}",
                    text=current_chunk.strip(),
                    source=source,
                    chunk_index=chunk_idx,
                    parent_text=parent_text.strip(),
                ))
                chunk_idx += 1

            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + sentence
            else:
                current_chunk = sentence

    if current_chunk.strip():
        chunks.append(DocumentChunk(
            chunk_id=f"{chunk_id_base}-chunk-{chunk_idx:04d}",
            text=current_chunk.strip(),
            source=source,
            chunk_index=chunk_idx,
            parent_text=current_chunk.strip(),  # last chunk, parent = self
        ))
        chunk_idx += 1

    return chunks


# ── Question chunks from JSON ───────────────────────────────────────────

def build_question_chunks(questions: List[dict]) -> List[DocumentChunk]:
    """Convert questions into searchable chunks."""
    chunks = []
    for i, q in enumerate(questions):
        qtype = q.get('type', 'single')
        qtype_label = {'single': '单选题', 'multiple': '多选题', 'truefalse': '判断题'}.get(qtype, qtype)

        options_text = []
        for k, v in q.get('options', {}).items():
            options_text.append(f"{k}. {v}")

        answer = q.get('answer', '')
        if qtype == 'truefalse':
            answer_text = '正确' if answer == 'A' else '错误'
        else:
            answer_text = '、'.join(q.get('options', {}).get(k, k) for k in answer)

        full_text = (
            f"[{qtype_label}] {q['question']}\n"
            f"选项：{'; '.join(options_text)}\n"
            f"答案：{answer_text}"
        )

        chunks.append(DocumentChunk(
            chunk_id=f"question-chunk-{q['id']:04d}",
            text=full_text,
            source="人工智能训练师初赛理论500题库",
            chunk_index=i,
            metadata={
                'question_id': q['id'],
                'type': qtype,
                'answer': answer,
            }
        ))

    return chunks


# ── Main loader ────────────────────────────────────────────────────────

def load_all_documents(doc_dir: str) -> List[DocumentChunk]:
    """Parse all documents in directory and return chunks."""
    all_chunks = []
    doc_path = Path(doc_dir)

    for filepath in doc_path.iterdir():
        fname = filepath.name.lower()

        if filepath.suffix.lower() in ('.doc',) and not fname.startswith('~'):
            print(f'[DocParser] Parsing .doc: {filepath.name}')
            with open(filepath, 'rb') as f:
                raw = f.read()

            # Strip %%TSD header if present
            ole2_magic = b'\xd0\xcf\x11\xe0'
            idx = raw.find(ole2_magic)
            if idx > 0:
                print(f'  Stripped %%TSD header at offset {idx}')
                raw = raw[idx:]

            text = _extract_text_from_doc(raw)
            if text.strip():
                chunks = chunk_text(text, source=filepath.name)
                all_chunks.extend(chunks)
                print(f'  Created {len(chunks)} chunks')
            else:
                print(f'  WARNING: No text extracted from {filepath.name}')

        elif filepath.suffix.lower() == '.pdf':
            print(f'[DocParser] Parsing PDF: {filepath.name}')
            text = _extract_text_from_pdf(str(filepath))
            chunks = chunk_text(text, source=filepath.name)
            all_chunks.extend(chunks)
            print(f'  Created {len(chunks)} chunks')

    return all_chunks


# ── Quick test ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    import json

    doc_dir = r'D:\work\idea\examjincompitition\doc'
    chunks = load_all_documents(doc_dir)

    print(f'\nTotal doc chunks: {len(chunks)}')

    # Also test question chunks
    qpath = r'D:\work\idea\examjincompitition\exam-site\backend\questions\questions.json'
    with open(qpath, encoding='utf-8') as f:
        questions = json.load(f)
    q_chunks = build_question_chunks(questions)
    print(f'Total question chunks: {len(q_chunks)}')
    print(f'Grand total: {len(chunks) + len(q_chunks)}')

    # Show samples
    for chunk in chunks[:3]:
        print(f'\n[{chunk.chunk_id}] source={chunk.source}')
        print(f'  {chunk.text[:200]}...')
