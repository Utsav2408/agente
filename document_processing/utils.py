from typing import List
from io import BytesIO
from langchain.schema import Document

from document_processing import chunking, embedding, google_drive_interact, pdf_utils
from faiss_ops import faiss_db
from mongo_ops import course_data
from pydantic_models.course_models import BookConfig, BookData


def process_books(
    course_id: str,
    config: BookConfig
) -> bool:

    try:
        # 1. Download the PDF into an in-memory buffer
        pdf_buffer: BytesIO = google_drive_interact.download_pdf_from_gdrive_in_memory(config.book_drive_link)

        # 2. Extract book data
        extracted_book_data: BookData = pdf_utils.extract_chapters_from_pdf(config, pdf_buffer)

        # 3. Insert to MongoDB true / false
        flag: bool = course_data.add_or_update_book(
            course_id,
            extracted_book_data
        )

        if flag:
            # 4. Chunk those chapters recursively
            docs: List[Document] = chunking.chunk_chapters_recursive(extracted_book_data, chunk_size=512, chunk_overlap=64)

            # 5. Embed all docs (using default model)
            embedded_docs = embedding.add_embeddings_to_documents(docs)

            # 6. Upsert into FAISS index + MongoDB
            faiss_db.create_faiss_store(course_id, extracted_book_data.book_id, embedded_docs)

            print(f"Successfully added Subject - {course_id} Book - {config.book_name}")
        else:
            print(f"Skipped Subject - {course_id} Book - {config.book_name}")
    except Exception as e:
        raise e
