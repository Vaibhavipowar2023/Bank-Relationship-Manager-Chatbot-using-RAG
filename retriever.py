import os
import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

EMBED_DIR = "embeddings"
INDEX_DIR = os.path.join(EMBED_DIR, "faiss_index")  # consistent name
DATA_DIR = "data"

CSV_FILES = [
    "account.csv",
    "client.csv",
    "loan.csv",
    "order.csv",
    "card.csv",
    "disposition.csv",
    "district.csv",
    "LuxuryLoanPortfolio.csv",
]


def _row_to_text(prefix, row):
    d = row.to_dict()
    return f"{prefix} | " + " ; ".join(f"{k}: {v}" for k, v in d.items())


def build_vectorstore(force_rebuild=False):
    """Build FAISS index from CSVs and save locally."""
    os.makedirs(EMBED_DIR, exist_ok=True)

    if os.path.exists(INDEX_DIR) and not force_rebuild:
        print("✅ Loading existing FAISS index from disk...")
        embeddings = OpenAIEmbeddings()
        return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

    print("🧠 Building new FAISS index from CSV files...")
    docs = []
    for f in CSV_FILES:
        path = os.path.join(DATA_DIR, f)
        if not os.path.exists(path):
            print(f"⚠️ {path} not found — skipping.")
            continue

        df = pd.read_csv(path, dtype=str).fillna("")
        prefix = f"file:{f}"
        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {f}"):
            docs.append(Document(page_content=_row_to_text(prefix, row), metadata={"source": f}))

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(INDEX_DIR)
    print("💾 FAISS index built and saved successfully.")
    return db


if __name__ == "__main__":
    print("⚙️ Running retriever locally (one-time build).")
    build_vectorstore(force_rebuild=True)
    print("✅ Done. Commit the 'embeddings/faiss_index' folder to GitHub.")
