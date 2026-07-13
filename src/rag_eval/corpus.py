"""Load a corpus of markdown documents and chunk them into retrievable units.

Documents are plain markdown files. Each document is split into paragraphs
(blank-line separated) and paragraphs are greedily packed into chunks of
roughly ``target_words`` words, without ever splitting a paragraph across two
chunks. Chunk IDs are stable across runs: ``"{doc_id}-{index}"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    path: Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    text: str
    position: int

    def word_count(self) -> int:
        return len(self.text.split())


def load_corpus(corpus_dir: str | Path) -> list[Document]:
    """Load every ``*.md`` file in ``corpus_dir`` as a Document.

    The document ID is the filename stem. The title is taken from the first
    Markdown H1 (``# Title``) if present, otherwise the stem.
    """
    corpus_dir = Path(corpus_dir)
    documents = []
    for path in sorted(corpus_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        doc_id = path.stem
        title = doc_id
        first_line = text.splitlines()[0] if text else ""
        if first_line.startswith("# "):
            title = first_line[2:].strip()
        documents.append(Document(doc_id=doc_id, title=title, text=text, path=path))
    return documents


def chunk_document(doc: Document, target_words: int = 300, max_words: int = 450) -> list[Chunk]:
    """Split a document into chunks by greedily packing paragraphs.

    Paragraphs are never split. A new paragraph is added to the current chunk
    unless doing so would exceed ``max_words`` and the current chunk already
    has at least one paragraph, in which case a new chunk starts.
    """
    paragraphs = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    # Drop a leading H1 title line if it stands alone as its own paragraph.
    if paragraphs and paragraphs[0].startswith("# "):
        paragraphs = paragraphs[1:]

    chunks: list[Chunk] = []
    current_paras: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current_paras, current_words
        if not current_paras:
            return
        text = "\n\n".join(current_paras)
        chunk_id = f"{doc.doc_id}-{len(chunks)}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                doc_title=doc.title,
                text=text,
                position=len(chunks),
            )
        )
        current_paras = []
        current_words = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_paras and current_words + para_words > max_words and current_words >= target_words:
            flush()
        current_paras.append(para)
        current_words += para_words

    flush()
    return chunks


def build_chunks(corpus_dir: str | Path, target_words: int = 300, max_words: int = 450) -> list[Chunk]:
    """Load a corpus directory and chunk every document."""
    documents = load_corpus(corpus_dir)
    chunks: list[Chunk] = []
    for doc in documents:
        chunks.extend(chunk_document(doc, target_words=target_words, max_words=max_words))
    return chunks
