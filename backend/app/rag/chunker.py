"""Legal-aware text chunker.

Splits on article boundaries when detectable ("Article 12", "Art. 12"), and falls
back to a sliding-window splitter for unstructured text. Keeps the detected
`article_ref` as metadata so retrieval can cite a precise article.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

ARTICLE_PATTERN = re.compile(
    r"(?im)^\s*(?:article|art\.?)\s*(\d+(?:[\-\. ]?\w+)?)\s*[:\-\.]?",
)


@dataclass
class Chunk:
    content: str
    article_ref: str | None
    chunk_index: int
    extra: dict


def _split_long(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def chunk_legal_text(text: str, max_chars: int = 1500) -> list[Chunk]:
    """Article-aware chunking. One Chunk per article, further split if too long."""
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        pieces = _split_long(text, max_chars=max_chars)
        return [Chunk(content=p, article_ref=None, chunk_index=i, extra={}) for i, p in enumerate(pieces)]

    chunks: list[Chunk] = []
    idx = 0
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        article_text = text[start:end].strip()
        article_ref = f"Article {m.group(1)}"
        if len(article_text) <= max_chars:
            chunks.append(Chunk(content=article_text, article_ref=article_ref, chunk_index=idx, extra={}))
            idx += 1
        else:
            for sub in _split_long(article_text, max_chars=max_chars):
                chunks.append(Chunk(content=sub, article_ref=article_ref, chunk_index=idx, extra={"split": True}))
                idx += 1
    return chunks
