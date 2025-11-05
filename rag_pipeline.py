# rag_pipeline.py
import os
import json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from retriever import build_vectorstore
from tools.interest_rate_tool import get_interest_rates
from tools.forex_tool import get_fx_rate
from tools.web_search_tool import web_search

# --- Load environment ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not set. Please export it before running.")

# --- Initialize LLM ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

# --- Prompt template ---
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

# ✅ Runnable pipeline replaces deprecated LLMChain
rag_chain = prompt | llm

# ✅ Cache FAISS vectorstore
VECTOR_DB = None

def load_or_create_vectorstore():
    global VECTOR_DB
    if VECTOR_DB is not None:
        return VECTOR_DB

    print("Loading FAISS vectorstore...")
    try:
        embeddings = OpenAIEmbeddings()
        VECTOR_DB = FAISS.load_local("embeddings/faiss_index", embeddings, allow_dangerous_deserialization=True)
        print("FAISS index loaded successfully.")
    except Exception:
        print("FAISS index not found — building from CSVs (first-time setup).")
        VECTOR_DB = build_vectorstore(force_rebuild=True)
    return VECTOR_DB


# --- Helper: convert tool data to natural language ---
def format_tool_output(tool_result):
    """Convert any structured result to a readable English sentence."""
    if tool_result is None:
        return "No data available."

    # If it's already a string, return it
    if isinstance(tool_result, str):
        return tool_result

    # Try to extract common patterns
    if isinstance(tool_result, dict):
        # Handle our interest rate structure
        data = tool_result.get("data") or {}
        if data:
            if isinstance(data, dict):
                parts = [f"{bank} offers around {rate}" for bank, rate in data.items()]
                return " ".join(parts) + "."
            if isinstance(data, list):
                return ", ".join(map(str, data))
        # Generic flattening
        return " ".join(f"{k}: {v}" for k, v in tool_result.items() if v and k != "status")

    # Handle list of dicts (e.g. web search)
    if isinstance(tool_result, list):
        summaries = []
        for item in tool_result[:3]:
            if isinstance(item, dict):
                text = item.get("snippet") or item.get("title") or str(item)
                summaries.append(text)
            else:
                summaries.append(str(item))
        return " ".join(summaries)

    # Fallback to JSON string
    return json.dumps(tool_result, indent=2)


# --- Main RAG answer function ---
def answer_with_rag(query, k=4):
    """Retrieve relevant info from FAISS + use LLM to answer."""
    db = load_or_create_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)

    context = "\n---\n".join([d.page_content for d in docs]) if docs else ""
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


# --- Main router ---
def handle_query(query):
    """Route query between RAG, tools, and web search."""
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
