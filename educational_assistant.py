import os
import glob
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from text_processor import TextProcessor
from vector_store import VectorStore
from llm_interface import LLMInterface
from config import Config
from database import Database
from user_manager import UserManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationalAssistant:
    """Main class for the AI Educational Assistant using RAG."""
    
    def __init__(self, 
                 db_type: str = "chroma",
                 embedding_model: str = None,
                 llm_model: str = None):
        """
        Initialize the Educational Assistant.
        
        Args:
            db_type: Type of vector database ("chroma" or "faiss")
            embedding_model: Model for generating embeddings
            llm_model: Model for generating answers
        """
        self.text_processor = TextProcessor()
        
        self.vector_store = VectorStore(
            db_type=db_type,
            embedding_model=embedding_model
        )
        
        self.llm_interface = LLMInterface(
            model_name=llm_model
        )
        
        # Initialize database and user manager
        self.db = Database()
        self.user_manager = UserManager(self.db)
        
        # Create necessary directories
        os.makedirs(Config.TEXTBOOKS_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
        logger.info("Educational Assistant initialized successfully")
    
    def load_textbooks(self, textbooks_dir: str = None) -> List[Dict[str, Any]]:
        """
        Load and process all textbooks from the specified directory.
        
        Args:
            textbooks_dir: Directory containing textbook files
            
        Returns:
            List of processing results for each textbook
        """
        textbooks_dir = textbooks_dir or Config.TEXTBOOKS_DIR
        results = []
        
        # Find all PDF and text files
        pdf_files = glob.glob(os.path.join(textbooks_dir, "**/*.pdf"), recursive=True)
        txt_files = glob.glob(os.path.join(textbooks_dir, "**/*.txt"), recursive=True)
        all_files = pdf_files + txt_files
        
        if not all_files:
            logger.warning(f"No textbook files found in {textbooks_dir}")
            return results
        
        logger.info(f"Found {len(all_files)} textbook files")
        
        for file_path in all_files:
            try:
                # Extract grade and subject from filename or path
                filename = os.path.basename(file_path)
                grade, subject = self._extract_metadata_from_filename(filename)
                
                # Process the textbook
                documents = self.text_processor.process_textbook(
                    file_path=file_path,
                    grade=grade,
                    subject=subject
                )
                
                results.append({
                    "file_path": file_path,
                    "grade": grade,
                    "subject": subject,
                    "documents_count": len(documents),
                    "status": "success"
                })
                
                logger.info(f"Processed {filename}: {len(documents)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "grade": None,
                    "subject": None,
                    "documents_count": 0,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def _extract_metadata_from_filename(self, filename: str) -> tuple:
        """Extract grade and subject from filename."""
        # Remove file extension
        name = os.path.splitext(filename)[0].lower()
        
        # Try to extract grade (1-10)
        grade = None
        for i in range(1, 11):
            if f"grade{i}" in name or f"class{i}" in name or f"std{i}" in name:
                grade = f"Grade {i}"
                break
        
        # Try to extract subject
        subjects = ["math", "science", "english", "history", "geography", "civics", "physics", "chemistry", "biology"]
        subject = None
        for subj in subjects:
            if subj in name:
                subject = subj.title()
                break
        
        return grade, subject
    
    def create_embeddings(self, documents: List) -> None:
        """
        Create embeddings for all documents and store in vector database.
        
        Args:
            documents: List of Document objects from text processing
        """
        try:
            if not documents:
                logger.warning("No documents provided for embedding creation")
                return
            
            logger.info(f"Creating embeddings for {len(documents)} documents")
            self.vector_store.create_vector_store(documents)
            logger.info("Embeddings created and stored successfully")
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    def store_in_vectordb(self, documents: List) -> None:
        """
        Store documents in vector database (alias for create_embeddings).
        
        Args:
            documents: List of Document objects
        """
        self.create_embeddings(documents)
    
    def retrieve_context(self, question: str, k: int = None, user_id: int = None) -> List:
        """
        Retrieve relevant context for a given question.
        
        Args:
            question: The question to find context for
            k: Number of documents to retrieve
            user_id: Optional user ID to filter by selected textbooks
            
        Returns:
            List of relevant documents
        """
        try:
            # Try to load existing vector store first
            if self.vector_store.vector_store is None:
                self.vector_store.load_existing_vector_store()
            
            if self.vector_store.vector_store is None:
                raise ValueError("No vector store available. Please load textbooks first.")
            
            # Apply user filtering if user_id is provided
            filter_dict = None
            if user_id:
                selected_paths = self.db.get_user_selected_textbook_paths(user_id)
                if selected_paths:
                    filter_dict = {"file_path": {"$in": selected_paths}}
                    logger.info(f"Filtering search to {len(selected_paths)} selected textbooks")
                else:
                    logger.warning(f"User {user_id} has no selected textbooks")
                    return []
            
            documents = self.vector_store.similarity_search(question, k=k, filter_dict=filter_dict)
            logger.info(f"Retrieved {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise
    
    def answer_question(self, question: str, k: int = None, user_id: int = None,
                       historical_context: str = None, 
                       current_session_context: List[Dict] = None) -> Dict[str, Any]:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: The question to answer
            k: Number of context documents to retrieve
            user_id: Optional user ID for personalized responses
            historical_context: Previous conversation summaries
            current_session_context: Recent Q&A from current session
            
        Returns:
            Dictionary containing answer and metadata
        """
        try:
            # Get user profile if user_id is provided
            user_class = None
            if user_id:
                profile = self.db.get_user_profile(user_id)
                if profile:
                    user_class = profile['class_grade']
            
            # Retrieve relevant context
            context_documents = self.retrieve_context(question, k=k, user_id=user_id)
            
            if not context_documents:
                if user_id:
                    return {
                        "answer": "I don't have enough information in your selected textbooks to answer this question. Please make sure you have selected the relevant textbooks for your subject.",
                        "sources": [],
                        "grades": [],
                        "subjects": [],
                        "context_documents_count": 0,
                        "model_used": self.llm_interface.model_name
                    }
                else:
                    return {
                        "answer": "I don't have enough information in my textbook database to answer this question. Please make sure relevant textbooks are loaded.",
                        "sources": [],
                        "grades": [],
                        "subjects": [],
                        "context_documents_count": 0,
                        "model_used": self.llm_interface.model_name
                    }
            
            # Generate answer using LLM with user's class information and conversation context
            result = self.llm_interface.answer_question(
                question, 
                context_documents, 
                user_class=user_class,
                historical_context=historical_context,
                current_session_context=current_session_context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            raise
    
    def setup_database(self, textbooks_dir: str = None) -> Dict[str, Any]:
        """
        Complete setup process: load textbooks, create embeddings, and store in vector database.
        
        Args:
            textbooks_dir: Directory containing textbook files
            
        Returns:
            Summary of the setup process
        """
        try:
            logger.info("Starting database setup...")
            
            # Load and process textbooks
            processing_results = self.load_textbooks(textbooks_dir)
            
            if not processing_results:
                return {"status": "error", "message": "No textbooks found to process"}
            
            # Collect all documents
            all_documents = []
            for result in processing_results:
                if result["status"] == "success":
                    # Re-process to get documents (in a real implementation, you'd store these)
                    file_path = result["file_path"]
                    grade = result["grade"]
                    subject = result["subject"]
                    
                    documents = self.text_processor.process_textbook(file_path, grade, subject)
                    all_documents.extend(documents)
            
            if not all_documents:
                return {"status": "error", "message": "No documents created from textbooks"}
            
            # Create embeddings and store in vector database
            self.create_embeddings(all_documents)
            
            summary = {
                "status": "success",
                "textbooks_processed": len([r for r in processing_results if r["status"] == "success"]),
                "total_documents": len(all_documents),
                "processing_results": processing_results
            }
            
            logger.info(f"Database setup completed: {summary['textbooks_processed']} textbooks, {summary['total_documents']} documents")
            return summary
            
        except Exception as e:
            logger.error(f"Error in database setup: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the current vector database."""
        try:
            if self.vector_store.vector_store is None:
                self.vector_store.load_existing_vector_store()
            
            if self.vector_store.vector_store is None:
                return {"status": "not_initialized", "message": "No vector database found"}
            
            # Get collection info (for Chroma)
            if hasattr(self.vector_store.vector_store, 'get'):
                collection = self.vector_store.vector_store.get()
                return {
                    "status": "initialized",
                    "db_type": self.vector_store.db_type,
                    "documents_count": len(collection['documents']) if collection['documents'] else 0,
                    "embedding_model": self.vector_store.embedding_model
                }
            else:
                return {
                    "status": "initialized",
                    "db_type": self.vector_store.db_type,
                    "embedding_model": self.vector_store.embedding_model
                }
                
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {"status": "error", "message": str(e)}
