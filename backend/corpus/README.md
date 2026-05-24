# Legal Corpus Directory

This directory contains legal documents for the RAG pipeline.

## Structure

```
corpus/
├── bns_2023/          # Bharatiya Nyaya Sanhita 2023 (replaces IPC)
│   └── *.txt          # Place BNS document(s) here
├── it_act_2000/       # Information Technology Act 2000
│   └── *.txt
└── pocso/             # POCSO Act
    └── *.txt
```

## Document Format

- Place plain text (.txt) files in the appropriate subdirectory
- The RAG pipeline chunks documents by ~500 characters with 50-char overlap
- Each chunk is embedded and stored in ChromaDB for semantic search
- Metadata (act name, source file) is preserved for citation

## Ingestion

After placing documents, trigger ingestion via:
```bash
# From the backend directory
python -c "
import asyncio
from app.services.ragService import RAGService
rag = RAGService()
result = asyncio.run(rag.ingest_corpus('./corpus'))
print(result)
"
```

## URL Ingestion (Public Legal Sources)

To ingest public legal sources from URLs (admin-only), call the API endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/legal/corpus/ingest-urls \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      {"url": "https://indiacode.nic.in/...", "act": "bns_2023"}
    ]
  }'
```

Use `RAG_ALLOWED_DOMAINS` in `.env` to allowlist trusted domains.
