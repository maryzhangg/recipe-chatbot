import weaviate

client = weaviate.Client("http://localhost:8080")

schema = {
    "classes": [
        {
            "class": "PDFChunk",
            "description": "Chunks of text extracted from PDFs",
            "vectorizer": "none",
            "properties": [
                {"name": "page", "dataType": ["int"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "source", "dataType": ["text"]}
            ]
        }
    ]
}

client.schema.delete_all()
client.schema.create(schema)
print("Weaviate schema created!")
