import os
import time
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import AzureSearch
from langchain.chains import RetrievalQA, LLMChain
from langchain.prompts import PromptTemplate

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment variables
        chat_endpoint = os.getenv("CHAT_AZURE_OAI_ENDPOINT")
        chat_key = os.getenv("CHAT_AZURE_OAI_KEY")
        chat_deployment = os.getenv("CHAT_AZURE_OAI_DEPLOYMENT")
        
        embedding_endpoint = os.getenv("EMBEDDING_AZURE_OAI_ENDPOINT")
        embedding_key = os.getenv("EMBEDDING_AZURE_OAI_KEY")
        embedding_deployment = os.getenv("EMBEDDING_AZURE_OAI_DEPLOYMENT")
        
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        search_index = os.getenv("AZURE_SEARCH_INDEX")
        
        api_version = os.getenv("AZURE_OAI_API_VERSION", "2023-09-01-preview")
        
        # System prompt

        system_prompt = """You are an expert AI assistant specializing in function optimization across programming languages.

        ## YOUR ROLE AND CAPABILITIES
        - You analyze code for performance bottlenecks and optimization opportunities
        - You provide advice on algorithm complexity improvements, memory usage optimization, and parallel processing
        - You have deep knowledge of language-specific optimization techniques across Python, JavaScript, C++, Java, Go, Rust, and other major languages
        - You understand both theoretical optimization principles and practical implementation details

        ## RESPONSE GUIDELINES
        - Start by identifying the core optimization problem or requirement
        - Provide clear, step-by-step explanations with technical justifications
        - Include concrete code examples that demonstrate the optimization techniques
        - Analyze the performance impact (time complexity, space complexity, resource usage) of your recommendations
        - When appropriate, offer multiple optimization approaches with their tradeoffs
        - Format your responses with clear headings, bullet points, and code blocks for readability
        - Be specific about which language your optimizations apply to

        ## CONSTRAINTS
        - When you don't have specific knowledge about an optimization technique, acknowledge your limitations
        - Prioritize proven optimization techniques over speculative approaches
        - Consider the maintenance and readability impact of your optimization suggestions
        - Do not suggest premature optimizations without clear performance benefits

        You are a specialized tool focused on helping users write more efficient code. Respond with practical, actionable optimization advice."""
        
        # Get user question
        user_question = input('\nEnter your function optimization question:\n')
        
        # Initialize embedding model
        logger.info("Initializing embedding model...")
        embedding_model = AzureOpenAIEmbeddings(
            deployment=embedding_deployment,
            api_key=embedding_key,
            azure_endpoint=embedding_endpoint,
            api_version=api_version
        )
        
        # Initialize vector store
        logger.info("Setting up vector store...")
        vector_store = AzureSearch(
            azure_search_endpoint=search_endpoint,
            azure_search_key=search_key,
            index_name=search_index,
            embedding_function=embedding_model.embed_query
        )
        
        # Initialize LLM
        logger.info("Initializing chat model...")
        llm = AzureChatOpenAI(
            azure_endpoint=chat_endpoint,
            api_version=api_version,
            deployment_name=chat_deployment,
            api_key=chat_key,
            temperature=0.5,
            max_tokens=1000
        )
        
        # Create RAG prompt
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
        
        # Create fallback prompt
        fallback_prompt = PromptTemplate(
            template="""
            {system_prompt}
            
            Question: {question}
            
            Answer:
            """,
            input_variables=["question"],
            partial_variables={"system_prompt": system_prompt}
        )
        
        # Try RAG first
        logger.info("Attempting to answer with RAG...")
        try:
            # Set up retriever
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            
            # Get documents
            docs = retriever.get_relevant_documents(user_question)
            
            # If documents were found, use RAG
            if docs:
                logger.info(f"Found {len(docs)} relevant documents. Using RAG.")
                
                # Create and run RAG chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                    chain_type_kwargs={"prompt": rag_prompt}
                )
                
                result = qa_chain({"query": user_question})
                response = result["result"]
                source = "RAG knowledge base"
            else:
                # No documents found, fall back to direct LLM
                logger.info("No relevant documents found. Using LLM's general knowledge.")
                
                # Create and run direct LLM chain
                fallback_chain = LLMChain(llm=llm, prompt=fallback_prompt)
                response = fallback_chain.run(question=user_question)
                source = "LLM's general knowledge"
                
        except Exception as e:
            # If any error occurs, fall back to direct LLM
            logger.error(f"Error in RAG processing: {str(e)}")
            logger.info("Falling back to LLM's general knowledge due to error.")
            
            # Create and run direct LLM chain
            fallback_chain = LLMChain(llm=llm, prompt=fallback_prompt)
            response = fallback_chain.run(question=user_question)
            source = "LLM's general knowledge (after error)"
        
        # Display response
        print("\nResponse:\n" + response + "\n")
        print(f"(Source: {source})")
        
    except Exception as ex:
        logger.error(f"An error occurred: {ex}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()