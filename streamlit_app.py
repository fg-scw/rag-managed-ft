import streamlit as st
import logging
from app import custom_rag_chain, retriever, init_db, process_files  # Importer les fonctions de app.py

# Configuration de la page Streamlit (doit être appelée en premier)
st.set_page_config(page_title="RAG Chatbot")

# Initialize logger for Streamlit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Appel de la fonction d'initialisation de la base de données
@st.cache_resource
def initialize_database():
    logger.info("Initializing the database...")
    init_db()  # Créer la table et activer l'extension vector
    process_files()  # Process the files and add embeddings
    logger.info("Database initialized and files processed.")

# Initialize the database once when Streamlit starts
initialize_database()

# Configuration de la barre latérale dans Streamlit
with st.sidebar:
    st.title('RAG Chatbot')

    # Ajouter un bouton pour rafraîchir l'ingestion des fichiers
    if st.button("Refresh Documents from S3"):
        with st.spinner("Ingesting new documents..."):
            process_files()
            st.success("Documents refreshed successfully!")

# Fonction pour générer la réponse via le RAG Chain
def generate_response(input):
    # Utilise le retriever et la chaîne RAG de app.py
    context = retriever.invoke(input)
    result = custom_rag_chain.invoke({
        "question": input,
        "context": context
    })
    return result

# Initialiser l'historique des messages dans la session si non présent
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome, ask me anything!"}]

# Afficher les messages du chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Récupérer l'entrée de l'utilisateur
if input := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": input})
    with st.chat_message("user"):
        st.write(input)

# Générer une nouvelle réponse si le dernier message n'est pas celui de l'assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(input)
            st.write(response)
    # Ajouter la réponse de l'assistant à l'historique
    st.session_state.messages.append({"role": "assistant", "content": response})