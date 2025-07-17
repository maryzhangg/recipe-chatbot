import os
import atexit
from pypdf import PdfReader
import weaviate
from weaviate.classes.config import Configure
from weaviate.classes.config import Property, DataType

# Connect to Weaviate REST endpoint
client = weaviate.connect_to_local()
atexit.register(client.close)  # Auto-close on exit

collection_name = "PDFChunk"

try:
    client.collections.delete(collection_name)
    print(f"Deleted existing collection: {collection_name}")
except Exception as e:
    print(f"Collection {collection_name} does not exist or error deleting: {e}")

# Check if collection exists
existing_collections = client.collections.list_all()
if collection_name not in existing_collections:
    client.collections.create(
        name=collection_name,
        properties=[
            Property(name="file_name", data_type=DataType.TEXT),
            Property(name="chunk_text", data_type=DataType.TEXT),
            Property(name="chunk_index", data_type=DataType.INT),
        ],
        vector_config=[
            Configure.Vectors.text2vec_ollama(
                name="pdf_vector",
                api_endpoint="http://host.docker.internal:11434",
                model="llama3.2:1b",
            )
        ],
    )

collection = client.collections.get(collection_name)

# Text chunking helper
def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# Load and index PDFs from the data/ folder
pdf_dir = "data"
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)
        reader = PdfReader(path)
        full_text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text.strip() + "\n"

        chunks = chunk_text(full_text)

        for idx, chunk in enumerate(chunks):
            collection.data.insert({
                "file_name": filename,
                "chunk_text": chunk,
                "chunk_index": idx,
            })

        print(f"✅ Loaded '{filename}' with {len(chunks)} chunks.")

print("✅ All PDFs processed and uploaded to Weaviate.")
