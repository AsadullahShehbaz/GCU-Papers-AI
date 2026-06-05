# ============================================================
# rag/chain.py — LangChain RAG Chain with Groq Streaming
# Retrieves relevant chunks → streams answer via Groq LLM
# ============================================================

import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from config import settings
from rag.vectorstore import search_similar

logger = logging.getLogger("gcul_api.rag.chain")

# ── Groq LLM ─────────────────────────────────────────────────
# streaming=True enables word-by-word streaming
def get_llm(streaming: bool = True) -> ChatGroq:
    return ChatGroq(
        model="llama3-70b-8192",
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
        max_tokens=1200,
        streaming=streaming,
    )


# ── RAG Prompt ────────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_template("""
You are an expert university tutor at GCU Lahore, Pakistan.
You are helping a student understand their past exam paper.

Subject:    {subject}
Department: {department}
Semester:   {semester}

Below are relevant excerpts from the actual exam paper:
---
{context}
---

Student's question:
{question}

Instructions:
- Answer based on the context above when relevant
- If the answer isn't in the context, use your knowledge but say so
- For math/CS problems: show full step-by-step working
- For theory: use bullet points with **bold** key terms
- Be concise, accurate, and exam-focused
- Use numbered steps for procedures
""")


# ── Format retrieved docs into a single context string ────────
def format_context(docs: list) -> str:
    """Join retrieved chunks with page numbers."""
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        parts.append(f"[Excerpt {i} — Page {page}]\n{doc.page_content}")
    return "\n\n".join(parts)


# ── Stream RAG answer ─────────────────────────────────────────
async def stream_rag_answer(
    collection_name: str,
    question: str,
    subject: str,
    department: str,
    semester: str,
):
    """
    Generator that yields answer tokens one by one.

    Usage in FastAPI:
        return StreamingResponse(
            stream_rag_answer(...),
            media_type="text/event-stream"
        )
    """
    logger.info(
        "CHAIN | Streaming answer  collection=%s  question='%s…'",
        collection_name, question[:50]
    )

    # 1. Retrieve relevant chunks from Qdrant
    docs = search_similar(collection_name, question, top_k=5)
    context = format_context(docs)

    logger.info("CHAIN | Retrieved %d chunks for context", len(docs))

    # 2. Build chain: prompt → LLM → string output
    chain = RAG_PROMPT | get_llm(streaming=True) | StrOutputParser()

    # 3. Stream tokens
    async for token in chain.astream({
        "context":    context,
        "question":   question,
        "subject":    subject,
        "department": department,
        "semester":   str(semester),
    }):
        # SSE format: "data: token\n\n"
        yield f"data: {token}\n\n"

    # Signal stream end
    yield "data: [DONE]\n\n"
    logger.info("CHAIN | Stream complete")