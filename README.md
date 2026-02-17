📄 README.md

# NCI Course Intelligence: Local RAG-based Semantic Search

An AI-powered document retrieval system designed to help international students navigate course information at the National College of Ireland (NCI). This project implements a full RAG (Retrieval-Augmented Generation) pipeline's retrieval stage, utilizing local embedding models and a vector database.

## Overview
Navigating hundreds of university web pages for specific course details can be overwhelming. This system scrapes 200+ NCI course pages, processes them into 758 semantic chunks, and allows users to find precise information through natural language queries rather than simple keyword matches.

## Tech Stack
* Language: Python 3.12 (Optimized for performance and stability)
* Vector Database: [ChromaDB](https://www.trychroma.com/) (Persistent local storage)
* Embedding Model: `all-MiniLM-L6-v2` via Sentence-Transformers (Efficient local inference)
* Data Processing: BeautifulSoup4 & JSONL for structured data management

## Project Structure
```text
NCIRag/
├── data/
│   ├── raw/           # Scraped raw HTML files
│   ├── chunks/        # Processed semantic chunks (chunks.jsonl)
│   └── chroma/        # Persistent Vector Database files
├── scripts/
│   ├── crawler.py     # Web scraping logic for NCI website
│   ├── build_chroma.py # Embedding generation and DB indexing
│   └── ask_chroma.py  # Local semantic search interface
├── requirements.txt   # Project dependencies
└── README.md          # Project documentation

⚙️ Key Features
Local-First Architecture: No external API dependencies (OpenAI/Anthropic) required for the retrieval stage, ensuring data privacy and zero cost.

Semantic Search: Uses vector embeddings to understand the intent behind a query (e.g., "How much does it cost?" matches with "Tuition Fees").

Source Transparency: Every search result provides a direct URL and metadata, preventing misinformation.

Optimized Chunking: Data is split into 758 distinct knowledge pieces to balance context density and retrieval accuracy.

🚀 Getting Started
Installation
Clone the repository:

Bash

git clone [https://github.com/willowkeem/NCIRag.git](https://github.com/willowkeem/NCIRag.git)
cd NCIRag
Set up a virtual environment and install dependencies:

Bash

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Usage
Run the interactive search tool:

Bash

python scripts/ask_chroma.py


📈 Future Roadmap
LLM Integration: Connecting OpenAI GPT-4 to generate conversational summaries from retrieved chunks.

Web UI: Developing a Streamlit-based interface for a better user experience.

Auto-Sync: Implementing a GitHub Action to re-crawl data monthly for updated fee information.