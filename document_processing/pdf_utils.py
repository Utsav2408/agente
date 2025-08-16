from io import BytesIO
from typing import List

import hashlib
from PyPDF2 import PdfReader

from constant.constant import HASH_ALGORITHM
from pydantic_models.course_models import BookConfig, BookData, ChapterData

_hasher = hashlib.new(HASH_ALGORITHM)        # fail fast if algo is wrong

def _compute_hash(text: str) -> str:
    h = _hasher.copy()
    h.update(text.encode("utf-8"))
    return h.hexdigest()

def extract_chapters_from_pdf(config: BookConfig, pdf_buffer: BytesIO) -> BookData:
    """Return a fully validated `BookData` built from the PDF and `BookConfig`."""
    pdf_buffer.seek(0)
    reader = PdfReader(pdf_buffer)

    chapters: List[ChapterData] = []
    num_pages = len(reader.pages)

    for chapter_cfg in config.chapters:
        if chapter_cfg.chapter_end_page > num_pages:
            raise ValueError(
                f"{chapter_cfg.chapter_title!r} ends at page "
                f"{chapter_cfg.chapter_end_page}, but PDF has only {num_pages} pages"
            )

        # 1-based → 0-based for start page; end page stays the same because
        # range() excludes it.
        page_text = "\n".join(
            (reader.pages[i].extract_text() or "")
            for i in range(chapter_cfg.chapter_start_page - 1, chapter_cfg.chapter_end_page)
        )

        chapters.append(
            ChapterData(
                chapter_title=chapter_cfg.chapter_title,
                chapter_start_page=chapter_cfg.chapter_start_page,
                chapter_end_page=chapter_cfg.chapter_end_page,
                chapter_content=page_text,
                chapter_hash=_compute_hash(page_text),
            )
        )

    def _slug(s: str) -> str:
        return "_".join(s.lower().split())

    return BookData(
        book_id=f"{_slug(config.book_name)}:{_slug(config.author_name)}",
        book_name=config.book_name,
        author_name=config.author_name,
        grade_ids=config.grade_ids,
        chapters=chapters,
    )
