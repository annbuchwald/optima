import os
import time
from dotenv import load_dotenv
import logging

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules from LangChain
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import AzureSearch
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def main():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Validate required environment variables
        required_env_vars = [
            "CHAT_AZURE_OAI_ENDPOINT", "CHAT_AZURE_OAI_KEY", "CHAT_AZURE_OAI_DEPLOYMENT",
            "EMBEDDING_AZURE_OAI_ENDPOINT", "EMBEDDING_AZURE_OAI_KEY", "EMBEDDING_AZURE_OAI_DEPLOYMENT",
            "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX"
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return
        
        # Retrieve configuration values
        chat_endpoint = os.getenv("CHAT_AZURE_OAI_ENDPOINT")
        chat_key = os.getenv("CHAT_AZURE_OAI_KEY")
        chat_deployment = os.getenv("CHAT_AZURE_OAI_DEPLOYMENT")
        
        embedding_endpoint = os.getenv("EMBEDDING_AZURE_OAI_ENDPOINT")
        embedding_key = os.getenv("EMBEDDING_AZURE_OAI_KEY")
        embedding_deployment = os.getenv("EMBEDDING_AZURE_OAI_DEPLOYMENT")
        
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        search_index = os.getenv("AZURE_SEARCH_INDEX")
        search_api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2023-07-01")
        
        oai_api_version = os.getenv("AZURE_OAI_API_VERSION", "2023-09-01-preview")
        
        # Log critical configuration (sensitive values omitted)
        logger.info(f"Chat endpoint: {chat_endpoint}")
        logger.info(f"Chat deployment: {chat_deployment}")
        logger.info(f"Embedding endpoint: {embedding_endpoint}")
        logger.info(f"Embedding deployment: {embedding_deployment}")
        logger.info(f"Search endpoint: {search_endpoint}")
        logger.info(f"Search index: {search_index}")
        logger.info(f"Search API version: {search_api_version}")
        logger.info(f"OpenAI API version: {oai_api_version}")
        
        # Validate Azure Search index name format
        if not search_index or not all(c.islower() or c.isdigit() or c == '-' for c in search_index) or search_index.startswith('-') or search_index.endswith('-'):
            logger.error(f"Invalid index format: {search_index}")
            return
        
        # Define system prompt for optimization assistant
        system_prompt = """You are an expert AI assistant specializing in function optimization across programming languages.
        (omitted for brevity, unchanged content)
        """
        
        # Prompt user for their optimization question
        user_question = input('\nEnter your function optimization question:\n')
        
        # Initialize Azure OpenAI embedding model
        logger.info("Initializing embedding model...")
        embedding_model = AzureOpenAIEmbeddings(
            deployment=embedding_deployment,
            api_key=embedding_key,
            azure_endpoint=embedding_endpoint,
            api_version=oai_api_version
        )
        
        # Initialize vector store object for Azure Cognitive Search
        vector_store = None
        
        logger.info("Testing Azure Search connection...")
        try:
            vector_store = AzureSearch(
                azure_search_endpoint=search_endpoint,
                azure_search_key=search_key,
                index_name=search_index,
                embedding_function=embedding_model.embed_query,
                api_version=search_api_version
            )
            
            # Perform a test similarity search to validate connection
            vector_store.similarity_search("test", k=1)
            logger.info("Successfully connected to Azure Search index.")
                
        except Exception as e:
            logger.error(f"Failed to connect to Azure Search index. Status code: {getattr(e, 'status_code', 'Unknown')}")
            logger.error(f"Response: {str(e)}")
            logger.error("Failed to connect to Azure Search. Please check your configuration.")
            vector_store = None
        
        # Initialize Azure OpenAI chat model
        logger.info("Initializing chat model...")
        llm = AzureChatOpenAI(
            azure_endpoint=chat_endpoint,
            api_version=oai_api_version,
            deployment_name=chat_deployment,
            api_key=chat_key,
            temperature=0.5,
            max_tokens=1000
        )
        
        # Define prompt templates for RAG and fallback
        rag_prompt = PromptTemplate(
            template="""
            {system_prompt}
            Question: {question}
            Context from relevant documentation:
            {context}
            Answer:
            """,
            input_variables=["context", "question"],
            partial_variables={"system_prompt": system_prompt}
        )
        
        fallback_prompt = PromptTemplate(
            template="""
            {system_prompt}
            Question: {question}
            Answer:
            """,
            input_variables=["question"],
            partial_variables={"system_prompt": system_prompt}
        )
        
        # Attempt Retrieval Augmented Generation if vector store is available
        if vector_store:
            logger.info("Attempting to answer with RAG...")
            try:
                retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                docs = retriever.get_relevant_documents(user_question)
                
                if docs:
                    logger.info(f"Found {len(docs)} relevant documents. Using RAG.")
                    
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=retriever,
                        chain_type_kwargs={"prompt": rag_prompt}
                    )
                    
                    result = qa_chain.invoke({"query": user_question})
                    response = result["result"]
                    source = "RAG knowledge base"
                else:
                    logger.info("No relevant documents found. Using LLM's general knowledge.")
                    response = (fallback_prompt | llm).invoke({"question": user_question})["text"]
                    source = "LLM's general knowledge"
                    
            except Exception as e:
                logger.error(f"Error in RAG processing: {str(e)}")
                logger.info("Falling back to LLM's general knowledge due to error.")
                response = (fallback_prompt | llm).invoke({"question": user_question})["text"]
                source = "LLM's general knowledge (after error)"
        else:
            logger.info("Vector store unavailable. Using LLM's general knowledge.")
            response = (fallback_prompt | llm).invoke({"question": user_question})["text"]
            source = "LLM's general knowledge (no vector store)"
        
        # Output the final response
        print("\nResponse:\n" + response + "\n")
        print(f"(Source: {source})")
        
    except Exception as ex:
        logger.error(f"An error occurred: {ex}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
