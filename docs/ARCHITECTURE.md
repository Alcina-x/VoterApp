# Architecture

The browser calls a FastAPI service. The service owns deterministic synthetic data, analytics, anomaly rules, audit logging, procedure retrieval, and report composition. The chat endpoint is a provider-neutral tool router: it detects a narrow intent, calls a read-only structured tool, and formats a grounded response. This keeps the LLM optional and prevents the model from becoming the source of truth.

The current deployment is intentionally local-first. PostgreSQL, an external LLM, and a vector database can be substituted behind the same service boundaries when production-like infrastructure is required for the academic evaluation.
