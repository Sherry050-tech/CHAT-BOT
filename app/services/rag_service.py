from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text


def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_text(text)


def embed_chunks(chunks):
    return embedder.encode(chunks)


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def retrieve_top_chunks(question, chunks, vectors, top_k=3):
    question_vector = embedder.encode(question)
    scored = []
    for chunk_text, chunk_vector in zip(chunks, vectors):
        score = cosine_similarity(question_vector, chunk_vector)
        scored.append((score, chunk_text))
    scored.sort(reverse=True)
    top_matches = scored[:top_k]
    return [text for score, text in top_matches]