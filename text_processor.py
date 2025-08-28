import os
import PyPDF2
import re
from typing import List, Dict, Any
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Handles text extraction from PDFs and text chunking."""
    
    def __init__(self):
        """Initialize TextProcessor without chunk size parameters since we're not using fixed-size chunks."""
        pass
    
    def count_words(self, text: str) -> int:
        """Count the number of words in a text string."""
        if not text:
            return 0
        # Split by whitespace and filter out empty strings
        words = [word for word in text.split() if word.strip()]
        return len(words)
    
    def split_text_into_chunks(self, text: str, chunk_size_words: int = 200000, overlap_words: int = 1000) -> List[str]:
        """Split text into chunks based on word count with overlap."""
        if not text:
            return []
        
        words = text.split()
        total_words = len(words)
        
        if total_words <= chunk_size_words:
            return [text]
        
        # Ensure overlap is less than chunk size to prevent infinite loops
        if overlap_words >= chunk_size_words:
            overlap_words = chunk_size_words // 2
        
        chunks = []
        start = 0
        
        while start < total_words:
            end = min(start + chunk_size_words, total_words)
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Calculate next start position
            # We want to move forward by (chunk_size - overlap) words
            step_size = chunk_size_words - overlap_words
            start = start + step_size
            
            # Break if we've reached the end
            if start >= total_words:
                break
            
            # Safety check: if we're creating too many chunks, break
            if len(chunks) > 50:  # Further reduced limit
                logger.warning(f"Too many chunks created ({len(chunks)}), stopping to prevent infinite loop")
                break
        
        return chunks
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                logger.info(f"Successfully extracted text from {pdf_path}")
                return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from a text file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read()
                logger.info(f"Successfully extracted text from {txt_path}")
                return text
        except Exception as e:
            logger.error(f"Error extracting text from {txt_path}: {str(e)}")
            raise
    
    def extract_title_from_title_pdf(self, directory_path: str) -> str:
        """Extract title from title.pdf file in the given directory."""
        title_pdf_path = os.path.join(directory_path, "title.pdf")
        
        if not os.path.exists(title_pdf_path):
            logger.warning(f"title.pdf not found in {directory_path}")
            # Return directory name as fallback
            directory_name = os.path.basename(directory_path)
            logger.info(f"Using directory name as title: {directory_name}")
            return directory_name
        
        try:
            title_text = self.extract_text_from_pdf(title_pdf_path)
            # Clean up the title text - take first few lines and clean whitespace
            lines = title_text.strip().split('\n')
            title = lines[0].strip() if lines else "Unknown Title"
            
            # If the extracted title is empty or just whitespace, use directory name
            if not title or title.isspace():
                directory_name = os.path.basename(directory_path)
                logger.info(f"Extracted title is empty, using directory name: {directory_name}")
                return directory_name
            
            logger.info(f"Extracted title: {title}")
            return title
        except Exception as e:
            logger.error(f"Error extracting title from {title_pdf_path}: {str(e)}")
            # Return directory name as fallback
            directory_name = os.path.basename(directory_path)
            logger.info(f"Using directory name as fallback title: {directory_name}")
            return directory_name
    
    def extract_last_two_digits(self, filename: str) -> str:
        """Extract the last 2 digits from filename before .pdf extension."""
        # Remove .pdf extension
        name_without_ext = filename.lower().replace('.pdf', '')
        
        # Check if the filename ends with exactly 2 digits
        match = re.search(r'(\d{2})$', name_without_ext)
        if match:
            return match.group(1)
        return None
    
    def create_source_name(self, directory_name: str, filename: str) -> str:
        """Create source name as directory_name + last_2_digits."""
        last_two_digits = self.extract_last_two_digits(filename)
        if last_two_digits:
            return f"{directory_name}{last_two_digits}"
        return None
    
    def process_directory(self, directory_path: str, grade: str = None, subject: str = None) -> List[Document]:
        """Process all PDF files in a directory and return documents with word count-based chunking."""
        documents = []
        
        # Extract title from title.pdf
        title_pdf = self.extract_title_from_title_pdf(directory_path)
        
        # Get directory name for source naming
        directory_name = os.path.basename(directory_path)
        
        # Get all PDF files in the directory (excluding title.pdf)
        pdf_files = []
        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.pdf') and filename.lower() != 'title.pdf':
                # Check if filename ends with 2 digits
                if self.extract_last_two_digits(filename):
                    pdf_files.append(filename)
                else:
                    logger.info(f"Skipping {filename} - does not end with 2 digits")
        
        logger.info(f"Found {len(pdf_files)} valid PDF files to process in {directory_path}")
        
        # Process each PDF file
        for filename in pdf_files:
            file_path = os.path.join(directory_path, filename)
            
            try:
                # Extract text from PDF
                text = self.extract_text_from_pdf(file_path)
                
                # Count words in the text
                word_count = self.count_words(text)
                logger.info(f"PDF {filename} contains {word_count} words")
                
                # Create base source name
                base_source_name = self.create_source_name(directory_name, filename)
                
                # Determine if chunking is needed
                if word_count <= 5000:
                    # Use current logic for PDFs with <= 5000 words
                    metadata = {
                        "source": base_source_name,
                        "grade": grade,
                        "subject": subject,
                        "file_path": file_path,
                        "title_pdf": title_pdf,
                        "word_count": word_count
                    }
                    
                    document = Document(
                        page_content=text,
                        metadata=metadata
                    )
                    
                    documents.append(document)
                    logger.info(f"Processed {filename} as single chunk ({word_count} words)")
                    
                else:
                    # Split large PDFs into chunks
                    logger.info(f"Splitting {filename} into chunks (exceeds 5000 words)")
                    chunks = self.split_text_into_chunks(text, chunk_size_words=5000, overlap_words=500)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_word_count = self.count_words(chunk)
                        chunk_source_name = f"{base_source_name}_{i}"
                        
                        metadata = {
                            "source": chunk_source_name,
                            "grade": grade,
                            "subject": subject,
                            "file_path": file_path,
                            "title_pdf": f"{title_pdf}_{i}",
                            "word_count": chunk_word_count,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "original_word_count": word_count
                        }
                        
                        document = Document(
                            page_content=chunk,
                            metadata=metadata
                        )
                        
                        documents.append(document)
                        logger.info(f"Processed {filename} chunk {i+1}/{len(chunks)} as {chunk_source_name} ({chunk_word_count} words)")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(documents)} documents from {directory_path}")
        return documents
    
    def process_textbook(self, file_path: str, grade: str = None, subject: str = None) -> List[Document]:
        """Process a single textbook file with word count-based chunking."""
        # Extract metadata
        filename = os.path.basename(file_path)
        
        # Extract text based on file type
        if file_path.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.txt'):
            text = self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Count words in the text
        word_count = self.count_words(text)
        logger.info(f"Textbook {filename} contains {word_count} words")
        
        # Determine if chunking is needed
        if word_count <= 5000:
            # Use current logic for files with <= 5000 words
            metadata = {
                "source": filename,
                "grade": grade,
                "subject": subject,
                "file_path": file_path,
                "title_pdf": "Single File Processing",
                "word_count": word_count
            }
            
            document = Document(
                page_content=text,
                metadata=metadata
            )
            
            logger.info(f"Processed {filename} as single document ({word_count} words)")
            return [document]
            
        else:
            # Split large files into chunks
            logger.info(f"Splitting {filename} into chunks (exceeds 5000 words)")
            chunks = self.split_text_into_chunks(text, chunk_size_words=5000, overlap_words=500)
            documents = []
            
            for i, chunk in enumerate(chunks):
                chunk_word_count = self.count_words(chunk)
                chunk_source_name = f"{filename}_{i}"
                
                metadata = {
                    "source": chunk_source_name,
                    "grade": grade,
                    "subject": subject,
                    "file_path": file_path,
                    "title_pdf": f"Single File Processing_{i}",
                    "word_count": chunk_word_count,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_word_count": word_count
                }
                
                document = Document(
                    page_content=chunk,
                    metadata=metadata
                )
                
                documents.append(document)
                logger.info(f"Processed {filename} chunk {i+1}/{len(chunks)} as {chunk_source_name} ({chunk_word_count} words)")
            
            return documents
