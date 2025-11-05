# retriever.py
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
DATA_DIR = "data"
CSV_FILES = [
    "account.csv",
    "client.csv",
    "loan.csv",
    "order.csv",
    "card.csv",
    "disposition.csv",
    "district.csv",
    "LuxuryLoanPortfolio.csv"
]

def _row_to_text(prefix, row):
    d = row.to_dict()
    pairs = [f"{k}: {v}" for k, v in d.items()]
    return f"{prefix} | " + " ; ".join(pairs)

def build_vectorstore(force_rebuild=False):
    os.makedirs(EMBED_DIR, exist_ok=True)
    index_path = os.path.join(EMBED_DIR, "faiss_index")

    if os.path.exists(index_path) and not force_rebuild:
        print("Loading existing FAISS index...")
        embeddings = OpenAIEmbeddings()
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        print("FAISS index loaded successfully.")
        return db

    print("Reading CSVs and building embeddings (this can take a few minutes)...")
    docs = []
    for f in CSV_FILES:
        path = os.path.join(DATA_DIR, f)
        if not os.path.exists(path):
            print(f"Warning: {path} not found — skipping.")
            continue

        df = pd.read_csv(path, dtype=str).fillna("")
        prefix = f"file:{f}"
        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {f}"):
            text = _row_to_text(prefix, row)
            docs.append(Document(page_content=text, metadata={"source": f}))

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(index_path)
    print("FAISS index built and saved.")
    return db

if __name__ == "__main__":
    build_vectorstore(force_rebuild=True)
