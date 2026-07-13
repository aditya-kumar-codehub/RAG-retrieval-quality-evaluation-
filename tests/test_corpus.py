import pytest

from rag_eval.corpus import Document, chunk_document


def make_doc(text: str, doc_id: str = "doc") -> Document:
    from pathlib import Path

    return Document(doc_id=doc_id, title=doc_id, text=text, path=Path(f"{doc_id}.md"))


def test_single_short_paragraph_is_one_chunk():
    doc = make_doc("This is a short paragraph with only a handful of words.")
    chunks = chunk_document(doc, target_words=300, max_words=450)
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc-0"
    assert chunks[0].doc_id == "doc"


def test_chunk_ids_are_stable_and_sequential():
    para = " ".join(["word"] * 200)
    text = "\n\n".join([para, para, para])  # ~600 words, should split
    doc = make_doc(text)
    chunks = chunk_document(doc, target_words=300, max_words=450)
    assert [c.chunk_id for c in chunks] == [f"doc-{i}" for i in range(len(chunks))]
    assert len(chunks) >= 2


def test_paragraphs_never_split_across_chunks():
    para_a = "Alpha " * 50
    para_b = "Beta " * 400  # forces a new chunk on its own
    para_c = "Gamma " * 50
    text = "\n\n".join([para_a, para_b, para_c])
    doc = make_doc(text)
    chunks = chunk_document(doc, target_words=300, max_words=450)
    # Every paragraph's full text should appear intact within exactly one chunk.
    for para in (para_a.strip(), para_b.strip(), para_c.strip()):
        containing = [c for c in chunks if para in c.text]
        assert len(containing) == 1


def test_leading_h1_title_is_dropped_from_chunks():
    doc = make_doc("# My Title\n\nSome body text here.")
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert "My Title" not in chunks[0].text
    assert "Some body text here." in chunks[0].text


def test_empty_document_produces_no_chunks():
    doc = make_doc("")
    chunks = chunk_document(doc)
    assert chunks == []


def test_chunk_word_count():
    doc = make_doc("one two three four five")
    chunks = chunk_document(doc)
    assert chunks[0].word_count() == 5
