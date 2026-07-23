from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from io import BytesIO
import numpy as np
from app.models import DocumentChunk
from app.crud import create_document_chunk

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def extract_text_from_pdf(file_source):
    reader = PdfReader(file_source)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text


def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_text(text)


def embed_chunks(chunks):
    return get_embedder().encode(chunks)


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def retrieve_top_chunks(question, chunks, vectors, top_k=3):
    question_vector = get_embedder().encode(question)
    scored = []
    for chunk_text, chunk_vector in zip(chunks, vectors):
        score = cosine_similarity(question_vector, chunk_vector)
        scored.append((score, chunk_text))
    scored.sort(reverse=True)
    top_matches = scored[:top_k]
    return [text for score, text in top_matches]

def process_uploaded_file(thread_id: str, filename: str, file_bytes: bytes) -> dict:
    file_source = BytesIO(file_bytes)
    text = extract_text_from_pdf(file_source)
    chunks = chunk_text(text)
    vectors = embed_chunks(chunks)

    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        document_chunk = DocumentChunk(
            thread_id=thread_id,
            source_filename=filename,
            chunk_text=chunk,
            embedding=vector.tolist(),
            chunk_index=index
        )
        create_document_chunk(document_chunk)

    return {"file_id": filename, "chunks_stored": len(chunks)}
