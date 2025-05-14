import os
import json
import time
from dotenv import load_dotenv, find_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from static_code_analyzer import *
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Updated imports using langchain_openai instead of langchain_community
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from openai import AzureOpenAI

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((Exception))  # Consider more specific exceptions
)
def get_embeddings_with_retry(embedding_model, text):
    try:
        logger.info("Attempting to get embeddings...")
        result = embedding_model.embed_query(text)
        logger.info("Successfully obtained embeddings")
        return result
    except Exception as e:
        logger.error(f"Error in getting embeddings: {str(e)}")
        raise

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        "CHAT_AZURE_OAI_ENDPOINT", 
        "CHAT_AZURE_OAI_KEY", 
        "CHAT_AZURE_OAI_DEPLOYMENT",
        "EMBEDDING_AZURE_OAI_ENDPOINT", 
        "EMBEDDING_AZURE_OAI_KEY", 
        "EMBEDDING_AZURE_OAI_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT", 
        "AZURE_SEARCH_KEY", 
        "AZURE_SEARCH_INDEX"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Log first few characters of the value for debugging
            logger.info(f"{var}: {value[:5]}{'*' * 10}")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def test_azure_search_connection(endpoint, key, index_name):
    """Test if the Azure Search index exists and is accessible."""
    import requests
    
    # Construct the URL to check if index exists
    url = f"{endpoint}/indexes/{index_name}?api-version=2023-07-01-Preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logger.info(f"Successfully connected to Azure Search index: {index_name}")
            return True
        else:
            logger.error(f"Failed to connect to Azure Search index. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception when testing Azure Search connection: {str(e)}")
        return False

def test_embedding_model(embedding_model):
    """Test if the embedding model works."""
    try:
        test_text = "This is a test."
        embeddings = embedding_model.embed_query(test_text)
        if embeddings and len(embeddings) > 0:
            logger.info(f"Successfully generated embeddings. Dimension: {len(embeddings)}")
            return True
        else:
            logger.error("Embedding model returned empty embeddings")
            return False
    except Exception as e:
        logger.error(f"Exception when testing embedding model: {str(e)}")
        return False

def getRespondFromAzureAI(user_question, ):
    pass

def main():
    try:
        # Configuration settingss
        logger.info("Loading environment variables...")
        env_path = find_dotenv(usecwd=True)
        if env_path:
            logger.info(f"Found .env file at: {env_path}")
        else:
            logger.warning("No .env file found. Using environment variables directly.")
        
        load_dotenv()
        
        # Validate environment variables
        validate_environment()
        
        # Chat model configuration
        chat_azure_endpoint = os.getenv("CHAT_AZURE_OAI_ENDPOINT")
        chat_azure_key = os.getenv("CHAT_AZURE_OAI_KEY")
        chat_azure_deployment = os.getenv("CHAT_AZURE_OAI_DEPLOYMENT")

        
        # Embedding model configuration
        embedding_azure_endpoint = os.getenv("EMBEDDING_AZURE_OAI_ENDPOINT")
        embedding_azure_key = os.getenv("EMBEDDING_AZURE_OAI_KEY")
        embedding_azure_deployment = os.getenv("EMBEDDING_AZURE_OAI_DEPLOYMENT")
        
        # Azure Search configuration
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        azure_search_key = os.getenv("AZURE_SEARCH_KEY")
        azure_search_index = os.getenv("AZURE_SEARCH_INDEX")
        
        # Test Azure Search connection
        logger.info("Testing Azure Search connection...")
        if not test_azure_search_connection(azure_search_endpoint, azure_search_key, azure_search_index):
            logger.error("Failed to connect to Azure Search. Please check your configuration.")
            return
        
        # API versions
        api_version = os.getenv("AZURE_OAI_API_VERSION", "2023-09-01-preview")
        logger.info(f"Using API version: {api_version}")
        
        # Show citations option
        show_citations = True
        
        # Hard-coded system prompt for function optimization
        system_prompt = """You are a specialized AI assistant focused on function optimization techniques across different programming languages.
        Your expertise includes:
        - Algorithm complexity analysis and optimization
        - Memory usage optimization
        - Parallel processing and concurrency
        - Language-specific optimization techniques (Python, Java, C++, JavaScript, etc.)
        - Performance profiling and bottleneck identification
        - Mathematical optimization approaches
        
        Analyze the user's function optimization question and provide:
        1. A clear explanation of the optimization technique(s) that would be most appropriate
        2. Code examples demonstrating the optimization when applicable
        3. Performance impact analysis of the suggested optimizations
        4. Language-specific considerations if relevant
        
        Base your answers on the retrieved documentation and best practices for function optimization.
        Cite sources when appropriate to support your recommendations.
        """
        
        # Get user question
        # user_question = input('\nEnter your function optimization question:\n')

        user_question = getAnalyzedCode()


        
        logger.info("Initializing embedding model...")
        # Initialize embedding model with its own endpoint and key
        embedding_model = AzureOpenAIEmbeddings(
            deployment=embedding_azure_deployment,
            api_key=embedding_azure_key,
            azure_endpoint=embedding_azure_endpoint,
            api_version=api_version
        )
        
        # Test embedding model
        logger.info("Testing embedding model...")
        if not test_embedding_model(embedding_model):
            logger.error("Failed to use embedding model. Please check your configuration.")
            return
        
        logger.info("Setting up vector store...")
        # Set up vector store with retry for embeddings
        try:
            vector_store = AzureSearch(
                azure_search_endpoint=azure_search_endpoint,
                azure_search_key=azure_search_key,
                index_name=azure_search_index,
                embedding_function=lambda text: get_embeddings_with_retry(embedding_model, text)
            )
            logger.info("Vector store setup successful")
        except Exception as e:
            logger.error(f"Failed to set up vector store: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise
        
        logger.info("Initializing chat model...")
        # Set up Azure OpenAI chat client with its own endpoint and key
        llm = AzureChatOpenAI(
            azure_endpoint=chat_azure_endpoint,
            api_version=api_version,
            deployment_name=chat_azure_deployment,
            api_key=chat_azure_key,
            temperature=0.5,
            max_tokens=1000
        )
        
        # Create prompt template that incorporates the system prompt
        prompt_template = """
        {system_prompt}
        
        Question: {question}
        
        Context from relevant documentation:
        {context}
        
        Answer:
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"],
            partial_variables={"system_prompt": system_prompt}
        )
        
        logger.info("Creating retrieval chain...")
        # Create retrieval chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=show_citations,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        logger.info("Processing your function optimization question...")
        logger.info(f"Question: {user_question}")
        
        # Add delay to avoid rate limits
        time.sleep(1)
        
        # Get response
        result = qa_chain({"query": user_question})
        
        # Display response
        print("\nResponse:\n" + result["result"] + "\n")
        
        # Display citations if enabled
        if show_citations and "source_documents" in result:
            print("Citations:")
            for i, doc in enumerate(result["source_documents"]):
                print(f"  Source {i+1}:")
                print(f"    Content: {doc.page_content[:150]}...")
                if hasattr(doc.metadata, 'source') and doc.metadata.source:
                    print(f"    Source: {doc.metadata.source}")
                print()
                
    except ValueError as ve:
        logger.error(f"Value error: {ve}")

    except Exception as ex:
        logger.error(f"An error occurred: {ex}")
        logger.error(f"Error type: {type(ex).__name__}")
        # Print traceback for detailed debugging
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()