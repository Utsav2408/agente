# app/utils/text_utils.py

import re
import os
from typing import List, Dict
from pdfminer.high_level import extract_text
from transformers import AutoTokenizer

# Load the tokenizer for all-MiniLM-L6-v2 once at import time
_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


# ─── 1) TEXT EXTRACTION ───────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Use pdfminer.six to extract ALL text from a PDF file.
    Returns a single string with raw text (including newlines).
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")
    return extract_text(pdf_path)


# ─── 2) CLEANING & NORMALIZATION ──────────────────────────────────────────────

def remove_hyphenated_line_breaks(text: str) -> str:
    """
    Replace occurrences like 'exam-\nple' → 'example', without removing genuine line breaks elsewhere.
    """
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)


def normalize_whitespace(text: str) -> str:
    """
    Collapse multiple spaces, tabs, and newlines into single spaces/newlines where appropriate.
    """
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse three or more newlines into exactly two newlines (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim trailing spaces on each line
    text = "\n".join([line.rstrip() for line in text.splitlines()])
    return text


def strip_headers_footers(raw_text: str) -> str:
    """
    Attempt to strip repeated first/last lines on each page, assuming pages were concatenated.
    Strategy:
      - Split by "" (form feed) which pdfminer sometimes leaves for page breaks.
      - If not present, split into pseudo-pages by double newline.
      - Remove any repeated first/last lines across pages (likely headers/footers).
    """
    if "" in raw_text:
        pages = raw_text.split("")
    else:
        pages = raw_text.split("\n\n")  # group into pseudo-pages by double newline

    # Identify potential headers/footers
    first_lines = [p.splitlines()[0] for p in pages if p.strip()]
    last_lines = [p.splitlines()[-1] for p in pages if p.strip()]
    repeated_headers = {line for line in first_lines if first_lines.count(line) > 1}
    repeated_footers = {line for line in last_lines if last_lines.count(line) > 1}

    cleaned_pages = []
    for p in pages:
        lines = p.splitlines()
        if lines and lines[0] in repeated_headers:
            lines = lines[1:]
        if lines and lines[-1] in repeated_footers:
            lines = lines[:-1]
        cleaned_pages.append("\n".join(lines))

    return "\n\n".join(cleaned_pages)


def clean_and_normalize(raw_text: str) -> str:
    """
    High-level cleaning pipeline for a section’s raw text:
      1) Remove hyphenated line breaks.
      2) Strip running headers/footers.
      3) Normalize whitespace.
    """
    step1 = remove_hyphenated_line_breaks(raw_text)
    step2 = strip_headers_footers(step1)
    step3 = normalize_whitespace(step2)
    return step3


# ─── 3) SECTION & SUBSECTION PARSING ──────────────────────────────────────────

# 1) Match a chapter heading that may appear as:
#    “1” on its own line (numeric-only) followed by the title on the next line,
#    OR “Chapter 1 <Title>” on a single line.
_CHAPTER_NUM_ONLY = re.compile(r"^\s*(\d+)\s*$")
_CHAPTER_SINGLE_LINE = re.compile(r"^\s*Chapter\s+(\d+)\s+(.*)$", re.IGNORECASE)

# 2) Match lines starting with a dotted number (e.g., “1.1”, “1.1.2”) followed by text.
_SECTION_DOTTED = re.compile(r"^\s*(\d+\.\d+(?:\.\d+)*)(?:[:\-]?\s*)(.+)$")


def split_into_sections(raw_text: str) -> List[Dict]:
    """
    Revised “split into sections” function to handle numeric-only headings like:
        • “1” (chapter number alone on a line) followed by “Introduction” on the next line
        • “1.1 What Is Data Mining?”
        • “1.1.1 Some Subsection Title”
        • “1.2 Motivating Challenges”
        • etc.

    Returns a list of dicts:
      [
        {
          "id":        "1",         # chapter-level if no “1.x” found before it
          "chapter":   1,
          "section":   1.0,
          "subsection": None,
          "title":     "Introduction",
          "parent":    "Chapter 1",   # or “1” if no explicit “Chapter 1” line
          "start_idx": <char offset in raw_text>
        },
        {
          "id":        "1.1",
          "chapter":   1,
          "section":   1.1,
          "subsection": None,
          "title":     "What Is Data Mining?",
          "parent":    "Chapter 1 – Introduction",
          "start_idx": <offset>
        },
        {
          "id":        "1.1.1",
          "chapter":   1,
          "section":   1.1,
          "subsection": 1.1,
          "title":     "Some Subsection Title",
          "parent":    "Section 1.1 – What Is Data Mining?",
          "start_idx": <offset>
        },
        ...
      ]

    If no “1.x” lines are found at all, returns a single pseudo-section for the whole chapter.
    """
    lines = raw_text.splitlines()
    sections = []
    chapter_num = None
    chapter_title = None

    # 1) First pass: locate a “Chapter N” heading
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Case A: “Chapter 1 <Title>” on one line
        m_single = _CHAPTER_SINGLE_LINE.match(line)
        if m_single:
            chapter_num = int(m_single.group(1))
            chapter_title = m_single.group(2).strip()
            chapter_start_idx = sum(len(ln) + 1 for ln in lines[:i])
            sections.append({
                "id": str(chapter_num),
                "chapter": chapter_num,
                "section": float(chapter_num),
                "subsection": None,
                "title": chapter_title,
                "parent": f"Chapter {chapter_num}",
                "start_idx": chapter_start_idx
            })
            i += 1
            break

        # Case B: standalone numeric line, e.g. “1”
        m_numonly = _CHAPTER_NUM_ONLY.match(line)
        if m_numonly:
            chapter_num = int(m_numonly.group(1))
            # Look ahead to next nonblank line for the actual title
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                chapter_title = lines[j].strip()
                chapter_start_idx = sum(len(ln) + 1 for ln in lines[:j])
                sections.append({
                    "id": str(chapter_num),
                    "chapter": chapter_num,
                    "section": float(chapter_num),
                    "subsection": None,
                    "title": chapter_title,
                    "parent": f"Chapter {chapter_num}",
                    "start_idx": chapter_start_idx
                })
                i = j + 1
                break
        i += 1

    # If no chapter-level heading was found, default to chapter 0 for entire text
    if chapter_num is None:
        chapter_num = 0
        chapter_title = "Full Chapter"
        sections.append({
            "id": "0",
            "chapter": 0,
            "section": 0.0,
            "subsection": None,
            "title": chapter_title,
            "parent": chapter_title,
            "start_idx": 0
        })
        i = 0  # scan from beginning for any “0.x” patterns
    # else: i points just after the chapter-level lines

    # 2) Second pass: scan remaining lines for “1.1 …”, “1.2 …”, “1.1.1 …” etc.
    while i < len(lines):
        line = lines[i]
        m_sec = _SECTION_DOTTED.match(line)
        if m_sec:
            sec_str = m_sec.group(1)       # e.g. "1.1" or "1.1.2"
            title_text = m_sec.group(2).strip()

            parts = sec_str.split(".")
            chap_of_sec = int(parts[0])
            # Only process if it matches our chapter_num
            if chap_of_sec == chapter_num:
                if len(parts) >= 3:
                    top_sec = float(f"{parts[0]}.{parts[1]}")
                    sub_sec = float(sec_str)
                else:
                    top_sec = float(sec_str)
                    sub_sec = None

                char_offset = sum(len(ln) + 1 for ln in lines[:i])
                parent = f"Chapter {chapter_num} – {chapter_title}"
                sections.append({
                    "id": sec_str,
                    "chapter": chap_of_sec,
                    "section": top_sec,
                    "subsection": sub_sec,
                    "title": title_text,
                    "parent": parent,
                    "start_idx": char_offset
                })
        i += 1

    return sections


def build_section_texts(raw_text: str, sections_meta: List[Dict]) -> List[Dict]:
    """
    Given raw_text and a list of section metadata (with 'start_idx'), build the
    uncleaned text for each section by slicing from start_idx to either the
    next section's start_idx or the end of raw_text.
    Returns a list of dicts with keys: id, chapter, section, subsection, title,
    parent, text, keywords.
    """
    results = []
    total_len = len(raw_text)

    for idx, meta in enumerate(sections_meta):
        start = meta["start_idx"]
        end = total_len if idx == len(sections_meta) - 1 else sections_meta[idx + 1]["start_idx"]
        section_text = raw_text[start:end].strip()
        results.append({
            "id": meta["id"],
            "chapter": meta["chapter"],
            "section": meta["section"],
            "subsection": meta["subsection"],
            "title": meta["title"],
            "parent": meta["parent"],
            "text": section_text,
            "keywords": []
        })

    return results


# ─── 4) PASSAGE (SLIDING WINDOW) SPLITTER ─────────────────────────────────────

def split_long_section_into_passages(
    section_id: str,
    section_text: str,
    max_tokens: int = 512,
    overlap: int = 64
) -> List[Dict]:
    """
    Use the all-MiniLM-L6-v2 tokenizer to split section_text into token IDs,
    then break into overlapping windows of size max_tokens (with overlap).
    Returns a list of dicts, each with:
      {
        "chunk_id": e.g. "1.1a",
        "parent_id": e.g. "1.1",
        "offset": <token offset>,
        "text": "<decoded text for that token window>"
      }
    """
    # Encode without special tokens to get raw token IDs
    token_ids = _tokenizer.encode(section_text, add_special_tokens=False)
    n_tokens = len(token_ids)

    if n_tokens <= max_tokens:
        # Decode entire token sequence back to text
        decoded = _tokenizer.decode(token_ids, skip_special_tokens=True).strip()
        return [{
            "chunk_id": f"{section_id}a",
            "parent_id": section_id,
            "offset": 0,
            "text": decoded
        }]

    passages = []
    step = max_tokens - overlap
    num_windows = ((n_tokens - max_tokens) // step) + 1

    for i in range(num_windows + 1):
        start_tok = i * step
        if start_tok >= n_tokens:
            break
        end_tok = min(start_tok + max_tokens, n_tokens)
        window_ids = token_ids[start_tok:end_tok]
        decoded = _tokenizer.decode(window_ids, skip_special_tokens=True).strip()
        suffix = chr(ord("a") + i)  # “a”, “b”, “c”, …
        passages.append({
            "chunk_id": f"{section_id}{suffix}",
            "parent_id": section_id,
            "offset": start_tok,
            "text": decoded
        })
        if end_tok == n_tokens:
            break

    return passages
