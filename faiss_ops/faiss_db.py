import os
import faiss
import pickle
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from constant.constant import EMBEDDING_MODEL, FAISS_INDEX_PATH, FAISS_METADATA_MAPPING_PATH
from mongo_ops import course_data

model = SentenceTransformer(EMBEDDING_MODEL)

def save_faiss_index(index: faiss.IndexFlatL2, index_path: str) -> None:
    """
    Write a FAISS IndexFlatL2 to disk.
    """
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    faiss.write_index(index, index_path)


def load_faiss_index(index_path: str) -> faiss.IndexFlatL2:
    """
    Load a FAISS index from disk as a memory-mapped index.
    """
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index file not found at: {index_path}")
    return faiss.read_index(index_path, faiss.IO_FLAG_MMAP)


def save_id_mapping(mapping: List[dict], mapping_path: str) -> None:
    """
    Serialize the list of doc_ids (in FAISS order) to disk via pickle.
    """
    os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
    with open(mapping_path, "wb") as f:
        pickle.dump(mapping, f)


def load_id_mapping(mapping_path: str) -> List[dict]:
    """
    Load the pickled list of doc_ids from disk.
    """
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"ID mapping file not found at: {mapping_path}")
    with open(mapping_path, "rb") as f:
        return pickle.load(f)


def create_faiss_store(
    course_id: str,
    book_id: str,
    new_docs: List[Document]
) -> None:

    embeddings_to_add: List[np.ndarray] = []
    metadata_to_add: List[str] = []

    # 1. Iterate over new_docs and insert into MongoDB only if unique
    for doc in new_docs:
        emb_list = doc.metadata.get("embedding")
        if emb_list is None:
            raise ValueError("Each Document must have metadata['embedding'] as a List[float].")
        emb_arr = np.array(emb_list, dtype="float32")
        embeddings_to_add.append(emb_arr)
        metadata_to_add.append({
            "book_name": doc.metadata.get("book_name"),
            "chapter_title": doc.metadata.get("chapter_title"),
            "chunk_content": doc.page_content
        })

    # Stack all embeddings-to-add into (M_new, D)
    embeddings_np = np.stack(embeddings_to_add, axis=0)
    dimension = embeddings_np.shape[1]

    faiss_index_file = f"{FAISS_INDEX_PATH}/{course_id}/{book_id}.faiss"
    metadata_file = f"{FAISS_METADATA_MAPPING_PATH}/{course_id}/{book_id}.pkl"


    # 3. Check if an existing index & mapping exist on disk
    if os.path.exists(
        f"{faiss_index_file}"
    ) and os.path.exists(
        f"{metadata_file}"
    ):
        os.remove(faiss_index_file)
        os.remove(metadata_file)
        print(f"Deleted existing FAISS index: {faiss_index_file}")
        print(f"Deleted existing metadata: {metadata_file}")

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    # 4. Persist index and id-mapping to disk
    save_faiss_index(index, faiss_index_file)
    save_id_mapping(metadata_to_add, metadata_file)

    return


def format_context_and_sources(results):
    context_chunks = []
    sources_set = set()  # to keep track of unique sources

    for doc, distance in results:
        context_chunks.append(doc["chunk_content"])
        book_name = doc["book_name"]
        chapter_title = doc["chapter_title"]
        sources_set.add(f"Book: {book_name}, Chapter: {chapter_title}")

    context = "\n\n".join(context_chunks)
    sources = list(sources_set)
    return context, sources


def format_context(results):
    context_chunks = []

    for doc, distance in results:
        context_chunks.append(doc["chunk_content"])

    context = "\n\n".join(context_chunks)
    return context


def retrieve_relevant_doc_subjective(
    course_name: List[str],
    grade: str,
    query: str,
    top_k: int = 5
):
    try:
        results: List[Tuple[dict, float]] = []
        q_vec = model.encode([query], convert_to_numpy=True).astype("float32")
        for course in course_name:
            books = course_data.get_books_for_course_and_grade(
                name=course, 
                grade=grade
            )
            for book in books:
                faiss_index_file = f"{FAISS_INDEX_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.faiss"
                metadata_file = f"{FAISS_METADATA_MAPPING_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.pkl"
                
                index = load_faiss_index(faiss_index_file)
                metadata = load_id_mapping(metadata_file)

                distances, indices = index.search(q_vec, top_k)
                distances = distances[0]
                indices = indices[0]
                
                for idx, dist in zip(indices, distances):
                    doc = metadata[idx]
                    if doc is not None:
                        results.append((doc, float(dist)))

        results.sort(key=lambda x: x[1])
        return format_context_and_sources(results)
    except Exception as e:
        print(e)
        raise e
    

def retrieve_relevant_context(
    course_name: List[str],
    grade: str,
    query: str,
    top_k: int = 5
):
    try:
        results: List[Tuple[dict, float]] = []
        q_vec = model.encode([query], convert_to_numpy=True).astype("float32")
        for course in course_name:
            books = course_data.get_books_for_course_and_grade(
                name=course, 
                grade=grade
            )
            for book in books:
                faiss_index_file = f"{FAISS_INDEX_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.faiss"
                metadata_file = f"{FAISS_METADATA_MAPPING_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.pkl"
                
                index = load_faiss_index(faiss_index_file)
                metadata = load_id_mapping(metadata_file)

                distances, indices = index.search(q_vec, top_k)
                distances = distances[0]
                indices = indices[0]
                
                for idx, dist in zip(indices, distances):
                    doc = metadata[idx]
                    if doc is not None:
                        results.append((doc, float(dist)))

        results.sort(key=lambda x: x[1])
        return format_context(results)
    except Exception as e:
        print(e)
        raise e
    

def retrieve_relevant_context_testing(
    course_name: List[str],
    grade: str,
    query: str,
    top_k: int = 5
):
    try:
        results: List[Tuple[dict, float]] = []
        q_vec = model.encode([query], convert_to_numpy=True).astype("float32")
        for course in course_name:
            books = course_data.get_books_for_course_and_grade(
                name=course, 
                grade=grade
            )
            for book in books:
                faiss_index_file = f"{FAISS_INDEX_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.faiss"
                metadata_file = f"{FAISS_METADATA_MAPPING_PATH}/{course.replace(' ', '_').lower()}/{book.book_id}.pkl"
                
                index = load_faiss_index(faiss_index_file)
                metadata = load_id_mapping(metadata_file)

                distances, indices = index.search(q_vec, top_k)
                distances = distances[0]
                indices = indices[0]
                
                for idx, dist in zip(indices, distances):
                    doc = metadata[idx]
                    if doc is not None:
                        results.append((doc, float(dist)))

        results.sort(key=lambda x: x[1])
        context_chunks = []

        for doc, distance in results:
            context_chunks.append(doc["chunk_content"])
        return context_chunks
    except Exception as e:
        print(e)
        raise e