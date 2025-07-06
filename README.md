# TrialReads

TrialReads is a Streamlit application that leverages LangChain and Perplexity AI to generate summaries of the first three chapters of books. This tool helps you decide whether to purchase a book by providing concise chapter-by-chapter summaries.**

## Features
- **Chapter Summaries**: Generate detailed summaries of the first three chapters of any book (~250 words per chapter)
- **Book Recommendations**: Get suggestions for similar books after generating summaries
- **Library Manager**: Chatbot interface to query your personal reading history
- Simple and intuitive user interface
- Powered by Perplexity AI's advanced language model capabilities


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

### Chapter Summaries & Recommendations
1. Open the application in your browser (usually at `http://localhost:8501`)
2. Enter your OpenAI API Key
3. Input the book title (e.g., "Pride and Prejudice") and author
4. Click **"Get Summary"** to generate chapter summaries
5. After summary generation, click **"Get Recommendations"** for 5 similar books

### Library Manager
1. Navigate to the **"Library Manager"** tab
2. Upload your book history CSV file with these columns:
   - `book_name`: Title of the book
   - `author`: Author's name
   - `status`: Reading status (`Reading`, `Yet to Buy`, `Ready to Start`, `Completed`)
   - `year_completed`: Year finished (leave blank for unread books)
3. Ask natural language questions in the chat interface:
   ```plaintext
   • "How many books by Dan Brown have I completed?"
   • "Show me books I finished in 2023"
   • "Which fantasy books am I currently reading?"
   • "List all unread books by female authors"


*You can install all dependencies using the provided requirements.txt.*

**Environment Variables**
The application uses an environment variable for securely handling the OpenAI API key. The key is entered via the UI and stored temporarily in os.environ.


### Contributing

**Contributions are welcome! If you'd like to improve this project, please follow these steps:**

- Fork this repository.

- Create a new branch for your feature or bug fix:


- git checkout -b feature-name

- Commit your changes and push them to your forked repository.

- Submit a pull request with a detailed description of your changes.

### Acknowledgments

- Streamlit for providing an easy-to-use framework for building web apps.

- LangChain for enabling seamless integration with LLMs.

- OpenAI API for their powerful LLM API.
