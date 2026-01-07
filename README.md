# LLM-Powered Data Intelligence Platform (SaaS)

Local-first platform that ingests SaaS data (users, events, subscriptions),
models it into a warehouse, defines a semantic layer (metrics),
and supports natural-language questions -> SQL -> results using an LLM with guardrails.

## Planned Stack (MVP)
- Postgres (warehouse)
- FastAPI (backend)
- Streamlit (UI)
- Chroma (vector store)

## Milestones
1. Repo + Docker services
2. Data ingestion + warehouse tables
3. Semantic layer (metrics)
4. RAG + NL->SQL + guardrails
5. UI demo + evaluation set
6. Spark/Kafka (optional extensions)
