import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv
from pydantic_models.course_models import BookData

load_dotenv()

def chunk_chapters_recursive(
    book_data: BookData, 
    chunk_size: int = int(os.getenv("CHUNK_SIZE")), 
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP"))
):
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],  # try paragraphs → lines → words → chars
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    all_chunks = []
    for chapter in book_data.chapters:
        # This will attempt to split at paragraph breaks first, then line breaks, etc.
        texts = splitter.split_text(chapter.chapter_content)
        for idx, chunk in enumerate(texts, start=1):
            metadata = {
                "book_name": book_data.book_name,
                "chapter_title": chapter.chapter_title,
                "id": f'{book_data.book_id}:{str(idx)}'
            }
            doc = Document(page_content=chunk, metadata=metadata)
            all_chunks.append(doc)

    return all_chunks
