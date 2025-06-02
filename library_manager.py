def library_management_system(user_query, headers):
    import os
    from langchain_community.chat_models import ChatOpenAI

    auth_header = headers.get("authorization", "")

    # If the header follows the 'Bearer <token>' format, split and get the token
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1]
    else:
        api_key = auth_header  # fallback if not in Bearer format

    os.environ["OPENAI_API_KEY"] = api_key

    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        StorageContext,
        load_index_from_storage,
    )
    PERSIST_DIR = "./storage"
    if not os.path.exists(PERSIST_DIR):
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(user_query)
    return str(response)