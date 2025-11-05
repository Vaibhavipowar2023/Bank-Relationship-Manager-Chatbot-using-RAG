
# 🏦 Bank Relationship Manager Chatbot using RAG

An intelligent **Bank Relationship Manager Chatbot** built with **Flask**, **LangChain**, and **OpenAI GPT-4o-mini**, designed to assist users with banking queries such as account details, loan information, forex conversions, and real-time interest rates.

This project demonstrates **Retrieval-Augmented Generation (RAG)** with integrated **real-time data tools**, giving the chatbot access to both static bank data and live financial information.

---

## 🚀 Features

✅ **Retrieval-Augmented Generation (RAG)** — answers banking questions using your internal CSV data  
✅ **Real-Time Tools Integration** — fetches latest forex rates and savings interest rates dynamically  
✅ **Web Search Fallback** — uses DuckDuckGo for answers not covered in data  
✅ **Clean Flask Backend** — lightweight and easy to deploy  
✅ **Modern White Chat UI** — minimal, responsive, and professional banking look  
✅ **FAISS Vector Store** — efficient semantic search across CSV data  

---

## 🧠 Tech Stack

| **Layer**           | **Technologies**                                                                 |
|----------------------|----------------------------------------------------------------------------------|
| **Frontend**         | HTML, CSS (white minimal UI), JavaScript                                        |
| **Backend**          | Python, Flask                                                                   |
| **AI / NLP**         | LangChain, OpenAI GPT-4o-mini                                                   |
| **Vector Database**  | FAISS                                                                           |
| **Data Sources**     | Bank CSV files (`account.csv`, `client.csv`, `loan.csv`, etc.)                  |
| **Real-Time Tools**  | Requests (Interest Rates, Forex), DuckDuckGo Search                             |

---
```
 🗂️ Project Structure
bank-rm-rag-vercel/
│
├── app.py                   # Flask entry point
├── retriever.py              # Builds FAISS embeddings from CSVs
├── rag_pipeline.py           # RAG + Tool routing logic
│
├── tools/
│   ├── interest_rate_tool.py # Fetches live savings interest rates
│   ├── forex_tool.py         # Fetches forex conversion rates
│   └── web_search_tool.py    # DuckDuckGo web search fallback
│
├── templates/
│   └── index.html            # Clean chat interface (white UI)
│
├── static/
│   ├── css/style.css         # Styling for chat UI
│   └── js/app.js             # Frontend message handling
│
├── data/                     # Bank CSV data files
├── embeddings/               # FAISS index (auto-generated)
│
├── requirements.txt
└── README.md

```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone this repository
```bash
git clone https://github.com/Vaibhavipowar2023/Bank-Relationship-Manager-Chatbot-using-RAG.git
cd Bank-Relationship-Manager-Chatbot-using-RAG
````

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate    # (Windows)
# or
source .venv/bin/activate   # (Mac/Linux)
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Add your environment variables

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=sk-your-key-here
```

### 5️⃣ Build the FAISS index (first run only)

```bash
python retriever.py
```

### 6️⃣ Run the chatbot

```bash
python app.py
```

Then open your browser and visit:
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 💬 Example Queries

* “What is client ID 104 loan amount?”
* “Convert 100 USD to INR”
* “What is the latest savings account interest rate?”
* “Show recent transactions for account 2001”
* “Who is the CEO of IDFC Bank?”

---

## 🧩 How It Works

1. **RAG Engine:**
   The chatbot retrieves relevant context from your local CSV data using FAISS embeddings.

2. **LLM Query:**
   GPT-4o-mini processes the question + context and generates an accurate answer.

3. **Real-Time Detection:**
   If a query requires live data (forex, rates, etc.), the model flags it, and the corresponding tool is invoked.

4. **Fallback Search:**
   If no internal context fits, the chatbot performs a web search for accurate answers.

---

## 🖥️ UI Preview

A clean, white, banking-grade chat interface with blue header and message timestamps.

```
User: What is the current savings account interest rate?
Bot: Based on the latest data, IDFC FIRST Bank offers around 3.00%–7.00%, 
     HDFC Bank 2.50%, and ICICI Bank 2.50%.
```

---

## 🛠️ Deployment Notes

To deploy this project on **Render**, **Vercel**, or any Flask-compatible platform:

* Expose `app.py` as the main entry point.
* Add your `.env` secrets in the hosting dashboard.
* Set build command:

  ```bash
  pip install -r requirements.txt
  ```
* Start command:

  ```bash
  python app.py
  ```

---

## 🔐 Security Notes

* **Never commit your `.env`** file or API keys.
* Add `.env` to your `.gitignore`.
* Regenerate keys immediately if exposed.



