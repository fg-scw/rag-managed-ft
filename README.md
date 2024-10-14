  # Simple RAG Pipeline on SCW

   # How to use it :
  - Add Instance to the private network (if you use private IPs)
  - git clone "repository"
  - chmod +x .install.sh
  - ./install.sh

   # Create .env file
    -# Scaleway API credentials
    SCW_ACCESS_KEY="COPY HERE YOUR ACCES KEY"
    SCW_SECRET_KEY="COPY HERE YOUR SECRET KEY"
    SCW_REGION="fr-par" 
    
    # Scaleway managed database (PostgreSQL) credentials
    SCW_DB_NAME="COPY HERE YOUR DB NAME"
    SCW_DB_USER="COPY HERE YOUR USER DB"
    SCW_DB_PASSWORD="COPY HERE YOUR PASSWORD"
    SCW_DB_HOST="172.16.8.4"  # The IP address of your database instance
    SCW_DB_PORT="5432"  # The port number for your database instance
    
    # Scaleway S3 bucket configuration
    SCW_BUCKET_NAME="COPY HERE YOUR BUCKET NAME"
    SCW_BUCKET_ENDPOINT="https://{{SCW_BUCKET_NAME}}.s3.{{SCW_REGION}}.scw.cloud"
  
    # Scaleway Inference API configuration (Embeddings)
    SCW_INFERENCE_EMBEDDINGS_ENDPOINT="https://e1b960b7-00a5-4cdb-a371-3eeb598820e3.ifr.fr-par.scaleway.com/v1"
  
    # Scaleway Inference API configuration (LLM deployment)
    SCW_INFERENCE_DEPLOYMENT_ENDPOINT="https://96ff2820-e07b-481e-91f8-ee49811cd2b3.ifr.fr-par.scaleway.com/v1" #llama3.1
    SCW_API_KEY="COPY HERE YOUR SECRET KEY"

   # Launch the Application 
  - streamlit run streamlite_app.py
