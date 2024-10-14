from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_community.document_loaders import S3FileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from botocore.client import Config
import psycopg2
import os
import boto3
import logging
import nltk


# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Establish connection to PostgreSQL database
def get_connection():
    try:
        conn = psycopg2.connect(
            database=os.getenv("SCW_DB_NAME"),
            user=os.getenv("SCW_DB_USER"),
            password=os.getenv("SCW_DB_PASSWORD"),
            host=os.getenv("SCW_DB_HOST"),
            port=os.getenv("SCW_DB_PORT")
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

# Initialize the database with the required tables and extensions
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Enable pgvector extension
        logger.info("Creating vector extension if it doesn't exist...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()

        # Create the object_loaded table
        logger.info("Creating table object_loaded if it doesn't exist...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS object_loaded (
                id SERIAL PRIMARY KEY,
                object_key TEXT
            );
        """)
        conn.commit()

    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Function to clean the documents table (for cleanup operations)
def clean_db():
    conn = get_connection()
    cur = conn.cursor()

    try:
        delete_query = "DELETE FROM documents"
        cur.execute(delete_query)
        conn.commit()
    except Exception as e:
        logger.error(f"Error cleaning the database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("SCW_API_KEY"),
    openai_api_base=os.getenv("SCW_INFERENCE_EMBEDDINGS_ENDPOINT"),
    model="sentence-transformers/sentence-t5-xxl",
    tiktoken_enabled=False,
)

# Create a PGVector store
connection_string = f"postgresql+psycopg2://{os.getenv('SCW_DB_USER')}:{os.getenv('SCW_DB_PASSWORD')}@{os.getenv('SCW_DB_HOST')}:{os.getenv('SCW_DB_PORT')}/{os.getenv('SCW_DB_NAME')}"
vector_store = PGVector(connection=connection_string, embeddings=embeddings)

# Ensure the bucket name is set correctly
endpoint_s3 = f"https://s3.{os.getenv('SCW_REGION', '')}.scw.cloud"
session = boto3.session.Session()
client_s3 = session.client(
    service_name='s3',
    endpoint_url=endpoint_s3,
    aws_access_key_id=os.getenv("SCW_ACCESS_KEY", ""),
    aws_secret_access_key=os.getenv("SCW_SECRET_KEY", "")
)

paginator = client_s3.get_paginator('list_objects_v2')
page_iterator = paginator.paginate(Bucket=os.getenv("SCW_BUCKET_NAME") # "rag-radio-france")

# Iterate through metadata and process files
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0, add_start_index=True, length_function=len, is_separator_regex=False)

# Function to process files from S3 and insert into the database
def process_files():
    conn = get_connection()
    cur = conn.cursor()

    try:
        for page in page_iterator:
            for obj in page.get('Contents', []):
                print(f"File found in S3 bucket: {obj['Key']}")
                cur.execute("SELECT object_key FROM object_loaded WHERE object_key = %s", (obj['Key'],))
                response = cur.fetchone()

                if response is None:
                    try:
                        file_loader = S3FileLoader(
                            bucket=os.getenv("SCW_BUCKET_NAME"), #"rag-radio-france",
                            key=obj['Key'],
                            endpoint_url=endpoint_s3,
                            aws_access_key_id=os.getenv("SCW_ACCESS_KEY", ""),
                            aws_secret_access_key=os.getenv("SCW_SECRET_KEY", "")
                        )
                        file_to_load = file_loader.load()

                        # Log that the file was loaded successfully and insert into database
                        cur.execute("INSERT INTO object_loaded (object_key) VALUES (%s)", (obj['Key'],))

                        # Initialize chunks as empty in case text splitting fails
                        chunks = text_splitter.split_text(file_to_load[0].page_content)

                        # Embed and store embeddings
                        if chunks:
                            embeddings_list = [embeddings.embed_query(chunk) for chunk in chunks]
                            vector_store.add_embeddings(chunks, embeddings_list)
                        else:
                            logger.error(f"No chunks to embed for file {obj['Key']}")

                    except Exception as e:
                        logger.error(f"An error occurred during file processing: {e}")

        conn.commit()

    except Exception as e:
        logger.error(f"An error occurred during the file processing: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Setup LLM for querying
llm = ChatOpenAI(
    base_url=os.getenv("SCW_INFERENCE_DEPLOYMENT_ENDPOINT"),
    api_key=os.getenv("SCW_SECRET_KEY"),
    model="meta/llama-3-8b-instruct:bf16"
)

# Define the RAG prompt template
prompt_template = """
Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Always finish your answer with "Thank you for asking".
{context}
Question: {question}
Helpful Answer:
"""
custom_rag_prompt = PromptTemplate.from_template(prompt_template)

# Setup retriever and custom RAG chain
retriever = vector_store.as_retriever()
custom_rag_chain = create_stuff_documents_chain(llm, custom_rag_prompt)
