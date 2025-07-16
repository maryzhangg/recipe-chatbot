import os
import fitz  # PyMuPDF
import weaviate
from sentence_transformers import SentenceTransformer

client = weaviate.Client("http://localhost:8080")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

PDF_FOLDER = "data/"

def extract_text_chunks(pdf_path, chunk_size=1000):
    doc = fitz.open(pdf_path)
    chunks = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        # Simple chunking by fixed length
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size].strip()
            if chunk:
                chunks.append({"page": page_num + 1, "content": chunk, "source": os.path.basename(pdf_path)})
    return chunks

def upload_chunks(chunks):
    for chunk in chunks:
        vector = embedder.encode(chunk["content"]).tolist()
        client.data_object.create(chunk, "PDFChunk", vector=vector)
    print(f"Uploaded {len(chunks)} chunks")

def main():
    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf"):
            print(f"Processing {filename}")
            path = os.path.join(PDF_FOLDER, filename)
            chunks = extract_text_chunks(path)
            upload_chunks(chunks)

if __name__ == "__main__":
    main()
