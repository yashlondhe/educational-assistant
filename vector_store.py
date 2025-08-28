import os
from typing import List, Dict, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """Handles vector database operations and embeddings."""
    
    def __init__(self, db_type: str = "chroma", embedding_model: str = None):
        self.db_type = db_type
        self.embedding_model = embedding_model or Config.EMBEDDING_MODEL
        self.embeddings = self._initialize_embeddings()
        self.vector_store = None
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            if self.embedding_model.startswith("text-embedding-"):
                # OpenAI embeddings
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OpenAI API key is required for OpenAI embeddings")
                return OpenAIEmbeddings(
                    model=self.embedding_model,
                    openai_api_key=Config.OPENAI_API_KEY
                )
            else:
                # HuggingFace embeddings
                return HuggingFaceEmbeddings(
                    model_name=self.embedding_model,
                    model_kwargs={'device': 'cpu'}
                )
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def create_vector_store(self, documents: List[Document], collection_name: str = "textbooks"):
        """Create a vector store from documents."""
        try:
            if self.db_type == "chroma":
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
                    collection_name=collection_name
                )
                # Persist the database
                self.vector_store.persist()
                logger.info(f"Created Chroma vector store with {len(documents)} documents")
                
            elif self.db_type == "faiss":
                self.vector_store = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )
                # Save the FAISS index
                self.vector_store.save_local("./faiss_index")
                logger.info(f"Created FAISS vector store with {len(documents)} documents")
                
            else:
                raise ValueError(f"Unsupported vector database type: {self.db_type}")
                
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def load_existing_vector_store(self, collection_name: str = "textbooks"):
        """Load an existing vector store."""
        try:
            if self.db_type == "chroma":
                self.vector_store = Chroma(
                    persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
                    embedding_function=self.embeddings,
                    collection_name=collection_name
                )
                logger.info("Loaded existing Chroma vector store")
                
            elif self.db_type == "faiss":
                if os.path.exists("./faiss_index"):
                    self.vector_store = FAISS.load_local(
                        folder_path="./faiss_index",
                        embeddings=self.embeddings
                    )
                    logger.info("Loaded existing FAISS vector store")
                else:
                    logger.warning("FAISS index not found, creating new one")
                    self.vector_store = None
                    
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Document]):
        """Add new documents to the existing vector store."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call create_vector_store or load_existing_vector_store first.")
        
        try:
            if self.db_type == "chroma":
                self.vector_store.add_documents(documents)
                self.vector_store.persist()
            elif self.db_type == "faiss":
                self.vector_store.add_documents(documents)
                self.vector_store.save_local("./faiss_index")
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """Search for similar documents."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        k = k or Config.TOP_K_RESULTS
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    def similarity_search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """Search for similar documents with similarity scores."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        k = k or Config.TOP_K_RESULTS
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Retrieved {len(results)} documents with scores for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search with score: {str(e)}")
            raise
