# rag_pipeline.py (safer for Render Free)
import os
import json
from typing import Optional

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

# If you keep a local builder, import it, but we won't run it unless allowed
from retriever import build_vectorstore  # your existing function

from tools.interest_rate_tool import get_interest_rates
from tools.forex_tool import get_fx_rate
from tools.web_search_tool import web_search

# ---------------- Config & Paths ----------------
# Where the prebuilt FAISS artifacts live. On Render, mount a disk to /var/data
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "embeddings")
INDEX_DIR = os.path.join(ARTIFACT_DIR, "faiss_index")  # directory produced by FAISS.save_local(...)
ALLOW_INDEX_BUILD = os.getenv("ALLOW_INDEX_BUILD", "0") == "1"  # default: DON'T build on server

OPENAI_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")  # small = cheaper/lighter

# ---------------- Lazy singletons ----------------
_llm: Optional[ChatOpenAI] = None
_embeddings: Optional[OpenAIEmbeddings] = None
_VECTOR_DB = None  # cached FAISS

def _get_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        # Don't explode at import-time; raise only on first real use
        raise EnvironmentError("OPENAI_API_KEY not set.")
    return key

def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0, openai_api_key=_get_openai_key())
    return _llm

def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(model=EMBED_MODEL, openai_api_key=_get_openai_key())
    return _embeddings

# ---------------- Prompt & chain ----------------
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a helpful and precise Bank Relationship Manager.\n"
        "Use the following context (if relevant) to answer the question.\n"
        "If it looks like the user is asking for real-time data (like current rates, forex, or recent changes), "
        "say 'NEEDS_REAL_TIME_DATA' in your response.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer clearly and accurately:"
    ),
)

def _get_rag_chain():
    # Build chain lazily so we don't construct LLM until needed
    return prompt | _get_llm()

# ---------------- Vector store loader ----------------
def load_or_create_vectorstore():
    """
    Load a prebuilt FAISS index. If it's missing:
      - Build only if ALLOW_INDEX_BUILD=1 (dangerous on 512MB).
      - Otherwise raise a clear error so you can prebuild offline.
    """
    global _VECTOR_DB
    if _VECTOR_DB is not None:
        return _VECTOR_DB

    print(f"Loading FAISS vectorstore from: {INDEX_DIR}")
    try:
        _VECTOR_DB = FAISS.load_local(
            INDEX_DIR,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        print("FAISS index loaded successfully.")
        return _VECTOR_DB
    except Exception as e:
        print("FAISS load failed:", e)

        if not ALLOW_INDEX_BUILD:
            # Do NOT build on server by default
            raise RuntimeError(
                "FAISS index not found. Prebuild it offline and place it under "
                f"{INDEX_DIR}. Or set ALLOW_INDEX_BUILD=1 (not recommended on low-RAM dynos)."
            )

        print("FAISS index not found — building from CSVs (server build allowed).")
        _VECTOR_DB = build_vectorstore(force_rebuild=True)
        return _VECTOR_DB

# ---------------- Helpers ----------------
def format_tool_output(tool_result):
    if tool_result is None:
        return "No data available."

    if isinstance(tool_result, str):
        return tool_result

    if isinstance(tool_result, dict):
        data = tool_result.get("data") or {}
        if data:
            if isinstance(data, dict):
                parts = [f"{bank} offers around {rate}" for bank, rate in data.items()]
                return " ".join(parts) + "."
            if isinstance(data, list):
                return ", ".join(map(str, data))
        return " ".join(f"{k}: {v}" for k, v in tool_result.items() if v and k != "status")

    if isinstance(tool_result, list):
        summaries = []
        for item in tool_result[:3]:
            if isinstance(item, dict):
                text = item.get("snippet") or item.get("title") or str(item)
                summaries.append(text)
            else:
                summaries.append(str(item))
        return " ".join(summaries)

    return json.dumps(tool_result, indent=2)

# ---------------- Core RAG ----------------
def answer_with_rag(query, k=4):
    db = load_or_create_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)

    context = "\n---\n".join([d.page_content for d in docs]) if docs else ""
    rag_chain = _get_rag_chain()
    resp = rag_chain.invoke({"context": context, "question": query})
    response_text = getattr(resp, "content", str(resp)).strip()

    needs_real_time = (
        "NEEDS_REAL_TIME_DATA" in response_text
        or any(
            key in query.lower()
            for key in ["current", "today", "rate", "interest", "forex", "convert", "price"]
        )
    )

    return {
        "answer": response_text,
        "needs_real_time": needs_real_time,
        "retrieved_docs": [d.metadata for d in docs],
    }

# ---------------- Router ----------------
def handle_query(query):
    rag_result = answer_with_rag(query)

    if rag_result["needs_real_time"]:
        q = query.lower()

        if "forex" in q or "exchange rate" in q or "convert" in q:
            fx = get_fx_rate(base="USD", target="INR")
            formatted = format_tool_output(fx)
            return {
                "source": "real_time_forex",
                "tool_result": formatted,
                "rag_answer": rag_result["answer"],
            }

        if "interest" in q or "rate" in q or "savings" in q or "loan rate" in q:
            rates = get_interest_rates()
            formatted = format_tool_output(rates)
            return {
                "source": "real_time_interest",
                "tool_result": formatted,
                "rag_answer": rag_result["answer"],
            }

        search_res = web_search(query)
        formatted = format_tool_output(search_res)
        return {
            "source": "web_search",
            "tool_result": formatted,
            "rag_answer": rag_result["answer"],
        }

    if len(rag_result["answer"].strip()) < 20:
        search_res = web_search(query)
        formatted = format_tool_output(search_res)
        return {
            "source": "web_search",
            "tool_result": formatted,
            "rag_answer": rag_result["answer"],
        }

    return {"source": "rag", "rag_answer": rag_result["answer"]}
