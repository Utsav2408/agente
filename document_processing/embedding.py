from typing import List
from sentence_transformers import SentenceTransformer, util
from langchain.schema import Document

from constant.constant import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)

def add_embeddings_to_documents(
    docs: List[Document]
) -> List[Document]:
    """
    Given a list of LangChain Document objects, compute embeddings for each
    document's page_content using SentenceTransformers, and return a new list
    of Documents where each metadata dict is updated with an 'embedding' key.

    Args:
        docs (List[Document]): List of Documents (with .page_content and .metadata)

    Returns:
        List[Document]: New list of Documents, each with metadata["embedding"] = vector.
    """

    # 2. Gather all texts and encode in one batch
    texts = [doc.page_content for doc in docs]
    embeddings = model.encode(texts, show_progress_bar=True)

    # 3. Construct new Document objects with embeddings in metadata
    docs_with_emb = []
    for doc, emb in zip(docs, embeddings):
        new_meta = dict(doc.metadata) if doc.metadata is not None else {}
        new_meta["embedding"] = emb.tolist()

        # Create a new Document with same content and updated metadata
        docs_with_emb.append(
            Document(page_content=doc.page_content, metadata=new_meta)
        )

    return docs_with_emb


def paragraph_similarity_pct(paragraph1: str, paragraph2: str) -> float:
    """
    Encode two paragraphs with MiniLM, compute cosine similarity,
    and return the similarity as a percentage (0-100).
    """

    # get embeddings as PyTorch tensors
    emb1 = model.encode(paragraph1, convert_to_tensor=True)
    emb2 = model.encode(paragraph2, convert_to_tensor=True)
    
    # cosine similarity returns a 1×1 tensor
    cos_sim = util.cos_sim(emb1, emb2).item()
    
    # clip to [0,1] in case of tiny numerical overshoot, then scale
    cos_sim = max(0.0, min(1.0, cos_sim))
    return round(cos_sim * 100.0)