** TrialReads

TrialReads is a Streamlit application that leverages LangChain and Perplexity AI to generate summaries of the first three chapters of books. This tool helps you decide whether to purchase a book by providing concise chapter-by-chapter summaries. **

### Features
- Generate detailed summaries of the first three chapters of any book

- Approximately 250 words per chapter summary

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

### Usage

- Open the application in your browser (usually at http://localhost:8501).

- Enter your Perplexity API Key in the provided field.

- Input the name of the book (e.g., "Pride and Prejudice", "Harry Potter and The Philosopher's Stone").

- Input the name of the author.

- Click on the "Get Summary" button to generate a short summary of the first 3 chapters of the book.

### Code Overview

The main functionality of the app is implemented in app.py. Here's a quick breakdown of its components:

**Streamlit UI:**

- Accepts user input for the Perplexity API key, the book name, and the author's name .

- Displays generated summaries or error messages.

**LangChain Integration:**

- Uses ChatPerplexity from LangChain's community package to interact with Perplexity's API.

**Error Handling:**

- Handles invalid API keys, missing inputs, and API response errors gracefully.

**Dependencies**
The application requires the following Python libraries:

- streamlit

- langchain-community

- langchain-core

- requests

*You can install all dependencies using the provided requirements.txt.*

**Environment Variables**
The application uses an environment variable for securely handling the Perplexity API key. The key is entered via the UI and stored temporarily in os.environ.

###Troubleshooting

**Common Errors:**
   401 Authorization Required:

- Ensure your Perplexity API key is valid and correctly entered.

- Verify that your account has sufficient credits.

**Empty Response:**

- Check if the model name you entered is supported by Perplexity's API.

**Application Not Running:**

- Ensure all dependencies are installed correctly.

- Verify that you're running Python 3.8 or higher.

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

- Perplexity AI for their powerful LLM API.
