from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.llms.openai import OpenAI
import chromadb
import os

def library_management_system(user_query, headers):
    
    # Fix protobuf compatibility issue
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
   
    auth_header = headers.get("authorization", "")

    # If the header follows the 'Bearer <token>' format, split and get the token
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1]
    else:
        api_key = auth_header  # fallback if not in Bearer format

    os.environ["OPENAI_API_KEY"] = api_key




    # Initialize ChromaDB (persistent client will create the db if it doesn't exist)
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection(name="library_manager")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    embed_model = OpenAIEmbedding(model_name="text-embedding-3-small")

    # Check if collection is empty (i.e., no documents have been processed)
    if chroma_collection.count() == 0:
        # Loading the pdf from local directory data
        documents = SimpleDirectoryReader("data").load_data()

        # Creating pipeline to break down documents into smaller chunks
        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(chunk_size=512, chunk_overlap=50),
                OpenAIEmbedding(model_name="text-embedding-3-small"),
            ],
            vector_store=vector_store,
        )

        nodes = pipeline.run(documents=documents)

    # Create index from vector store (works whether collection is new or existing)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    llm = OpenAI(model="gpt-4o-mini", temperature=0.1)   
    query_engine = index.as_query_engine(
        llm=llm,
        response_mode="tree_summarize",
    )
    response = query_engine.query(user_query)
    return str(response)