# TrialReads

TrialReads is a Streamlit application that leverages LangChain/LangGraph, LlamaIndex, and OpenAI to help you decide whether to read a book. You interact through a **single chat box**: a tool-calling agent reads each message and decides on its own whether to summarize a book or answer a question about your personal library — no tabs or mode switches.

## Features
- **Conversational agent**: One chat interface backed by a LangGraph ReAct agent that automatically picks the right tool for each message (or just answers directly).
- **Chapter Summaries**: Ask for a summary and get the first three chapters of any book summarized chapter by chapter (~250 words per chapter).
- **Book Recommendations**: After a summary is generated, a **"Get Book Recommendations"** button appears that suggests 5 similar books, each with an Amazon purchase link.
- **Library Manager (text-to-SQL)**: Ask natural-language questions about your personal reading history; the question is translated into SQL and run against your structured spreadsheet (`data/Books.xlsx`) for exact answers.
- Powered by OpenAI's `gpt-4o-mini` model.


### Installation
Follow these steps to set up and run the application locally:

1. Clone the Repository
   
`git clone https://github.com/your-username/trial-reads.git
cd trial-reads`

2. Create a Virtual Environment

`python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate`

3. Install Dependencies
Install the required Python packages using pip:

`pip install -r requirements.txt`

4. Run the Application
Start the Streamlit app:

`streamlit run app.py`

## Usage

Open the application in your browser (usually at `http://localhost:8501`) and type into the chat box. The agent decides what to do based on what you ask — you don't pick a mode.

> The OpenAI API key is read from a `.env` file (see **Environment Variables** below), not entered in the UI.

### Chapter Summaries & Recommendations
1. Ask for a summary, e.g. *"Summarize the first three chapters of Pride and Prejudice."* (You can name the author, but the agent will fill it in from its own knowledge if you don't.)
2. The agent calls its summary tool and returns a chapter-by-chapter summary.
3. A **"Get Book Recommendations"** button appears beneath the summary — click it to get 5 similar books, each with a **"Buy on Amazon"** link.

### Library Manager (text-to-SQL)
Ask natural-language questions about your own reading history and the agent routes them to the library tool, which answers from your structured spreadsheet (`data/Books.xlsx`, with columns `Book`, `Author`, `Status`, `Year`) by translating your question into SQL. Because counts, filters, and aggregates run as real queries over the whole table, the answers are exact. Examples:

```plaintext
• "How many books did I read in 2024?"
• "How many books are in my 'Yet to Buy' category?"
• "Which books by Dan Brown have I finished?"
```

On each query the spreadsheet is loaded into a fresh SQLite database (`data/library.db`), so any edits you make to `data/Books.xlsx` are reflected immediately — no re-indexing step. The generated SQL is logged for each query so you can see exactly what ran.

### Other questions
If a message is neither a book summary request nor a library question, the agent simply answers it directly.

*You can install all dependencies using the provided requirements.txt.*

**Environment Variables**
The application reads the OpenAI API key from an environment variable. Copy `.env.example` to `.env` in the project root and set your key:

```
OPENAI_API_KEY=your-openai-api-key-here
```

`load_dotenv()` loads this at startup. The `.env` file is gitignored and must never be committed.


### Contributing

**Contributions are welcome! If you'd like to improve this project, please follow these steps:**

- Fork this repository.

- Create a new branch for your feature or bug fix:


- git checkout -b feature-name

- Commit your changes and push them to your forked repository.

- Submit a pull request with a detailed description of your changes.

### Acknowledgments

- Streamlit for providing an easy-to-use framework for building web apps.

- LangChain / LangGraph for the tool-calling agent and LLM integration.

- LlamaIndex for the text-to-SQL library search.

- OpenAI API for their powerful LLM.
