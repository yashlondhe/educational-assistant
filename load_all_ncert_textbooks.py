#!/usr/bin/env python3
"""
Load ALL documents from NCERT_Textbooks directory into Chroma database
"""

import os
import shutil
import sys
from text_processor import TextProcessor
from vector_store import VectorStore
from collections import defaultdict
from langchain.schema import Document

def clean_chroma_database():
    """Clean the Chroma database by removing the directory."""
    chroma_dir = "./chroma_db"
    
    if os.path.exists(chroma_dir):
        try:
            shutil.rmtree(chroma_dir)
            print(f"✅ Cleaned Chroma database: {chroma_dir}")
            return True
        except Exception as e:
            print(f"❌ Error cleaning database: {str(e)}")
            return False
    else:
        print(f"ℹ️  Chroma database directory not found: {chroma_dir}")
        return True

def find_all_textbook_directories():
    """Find all directories that contain PDF files in NCERT_Textbooks."""
    ncert_dir = "NCERT_Textbooks"
    
    if not os.path.exists(ncert_dir):
        print(f"❌ NCERT_Textbooks directory not found: {ncert_dir}")
        return []
    
    textbook_dirs = []
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(ncert_dir):
        # Check if this directory contains PDF files (excluding title.pdf)
        pdf_files = [f for f in files if f.lower().endswith('.pdf') and f.lower() != 'title.pdf']
        
        if pdf_files:
            # Check if any PDF files end with 2 digits
            valid_pdfs = []
            for pdf in pdf_files:
                # Simple check for 2 digits at the end
                name_without_ext = pdf.lower().replace('.pdf', '')
                if name_without_ext[-2:].isdigit():
                    valid_pdfs.append(pdf)
            
            if valid_pdfs:
                textbook_dirs.append({
                    'path': root,
                    'pdf_files': valid_pdfs,
                    'total_pdfs': len(valid_pdfs)
                })
    
    return textbook_dirs

def extract_grade_and_subject_from_path(directory_path):
    """Extract grade and subject from directory path."""
    path_parts = directory_path.split(os.sep)
    
    # Find grade (class1, class2, etc.)
    grade = None
    subject = None
    
    for i, part in enumerate(path_parts):
        if part.startswith('class'):
            grade = part
            # The subject is the next directory after the class directory
            if i + 1 < len(path_parts):
                subject_raw = path_parts[i + 1]
                # Convert hyphens to spaces and capitalize
                subject = subject_raw.replace('-', ' ').title()
            break
    
    return grade, subject

def process_all_textbooks():
    """Process all textbook directories and return all documents."""
    
    print("🔄 Processing All NCERT Textbooks")
    print("=" * 40)
    
    # Initialize text processor
    processor = TextProcessor()
    
    # Find all textbook directories
    textbook_dirs = find_all_textbook_directories()
    
    if not textbook_dirs:
        print("❌ No valid textbook directories found!")
        return []
    
    print(f"📚 Found {len(textbook_dirs)} textbook directories")
    
    # Show directory structure
    print(f"\n📁 Textbook Directory Structure:")
    for i, dir_info in enumerate(textbook_dirs, 1):
        grade, subject = extract_grade_and_subject_from_path(dir_info['path'])
        print(f"   {i}. {dir_info['path']}")
        print(f"      Grade: {grade or 'Unknown'}, Subject: {subject or 'Unknown'}")
        print(f"      PDFs: {dir_info['total_pdfs']}")
    
    # Process all directories
    all_documents = []
    stats = defaultdict(int)
    
    print(f"\n🔄 Processing directories...")
    
    for i, dir_info in enumerate(textbook_dirs, 1):
        directory_path = dir_info['path']
        grade, subject = extract_grade_and_subject_from_path(directory_path)
        
        print(f"\n📁 Processing {i}/{len(textbook_dirs)}: {directory_path}")
        print(f"   Grade: {grade or 'Unknown'}, Subject: {subject or 'Unknown'}")
        
        try:
            # Process the directory
            documents = processor.process_directory(
                directory_path=directory_path,
                grade=grade,
                subject=subject
            )
            
            all_documents.extend(documents)
            
            # Update stats
            stats[f"{grade}_{subject}"] += len(documents)
            
            print(f"   ✅ Processed {len(documents)} documents")
            
        except Exception as e:
            print(f"   ❌ Error processing {directory_path}: {str(e)}")
            continue
    
    print(f"\n📊 Processing Summary:")
    print(f"   Total directories processed: {len(textbook_dirs)}")
    print(f"   Total documents: {len(all_documents)}")
    
    print(f"\n📈 Documents by Grade/Subject:")
    for key, count in sorted(stats.items()):
        print(f"   {key}: {count} documents")
    
    return all_documents

def load_to_vector_database(documents):
    """Load all documents to the vector database in batches."""
    
    if not documents:
        print("❌ No documents to load!")
        return False
    
    print(f"\n📚 Loading {len(documents)} documents to Chroma database...")
    
    # Initialize vector store
    vector_store = VectorStore(db_type="chroma")
    
    # Process in smaller batches to avoid memory issues
    batch_size = 20  # Reduced from 50 to 20 for lower memory usage
    total_batches = (len(documents) + batch_size - 1) // batch_size
    
    print(f"📦 Processing in {total_batches} batches of {batch_size} documents each")
    
    try:
        for i in range(0, len(documents), batch_size):
            batch_num = (i // batch_size) + 1
            batch_docs = documents[i:i + batch_size]
            
            print(f"   📦 Processing batch {batch_num}/{total_batches} ({len(batch_docs)} documents)")
            
            if batch_num == 1:
                # First batch: create new vector store
                vector_store.create_vector_store(batch_docs)
            else:
                # Subsequent batches: add to existing store
                vector_store.add_documents(batch_docs)
            
            print(f"   ✅ Completed batch {batch_num}")
        
        print("✅ Successfully loaded all documents to Chroma database!")
        return True
    except Exception as e:
        print(f"❌ Error loading to vector database: {str(e)}")
        return False

def process_directory_file_by_file(processor, vector_store, directory_path, grade, subject, is_first_directory=False):
    """Process a directory file by file to minimize memory usage."""
    
    print(f"   📁 Processing directory file by file: {directory_path}")
    
    # Get all PDF files in the directory (excluding title.pdf)
    pdf_files = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf') and filename.lower() != 'title.pdf':
            # Check if filename ends with 2 digits
            name_without_ext = filename.lower().replace('.pdf', '')
            if name_without_ext[-2:].isdigit():
                pdf_files.append(filename)
    
    if not pdf_files:
        print(f"   ⚠️  No valid PDF files found in {directory_path}")
        return 0
    
    print(f"   📚 Found {len(pdf_files)} PDF files to process")
    
    # Extract title from title.pdf
    title_pdf = processor.extract_title_from_title_pdf(directory_path)
    directory_name = os.path.basename(directory_path)
    
    processed_count = 0
    
    for i, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(directory_path, filename)
        
        print(f"      📄 Processing file {i}/{len(pdf_files)}: {filename}")
        
        try:
            # Extract text from PDF
            text = processor.extract_text_from_pdf(file_path)
            
            # Count words in the text
            word_count = processor.count_words(text)
            print(f"         📊 Word count: {word_count}")
            
            # Create base source name
            base_source_name = processor.create_source_name(directory_name, filename)
            
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
                
                # Load single document immediately
                if is_first_directory and i == 1:
                    # First file of first directory: create new vector store
                    vector_store.create_vector_store([document])
                else:
                    # Add to existing store
                    vector_store.add_documents([document])
                
                processed_count += 1
                print(f"         ✅ Processed as single chunk")
                
            else:
                # Split large PDFs into chunks
                print(f"         🔄 Splitting into chunks (exceeds 5000 words)")
                chunks = processor.split_text_into_chunks(text, chunk_size_words=5000, overlap_words=500)
                
                chunk_documents = []
                for j, chunk in enumerate(chunks):
                    chunk_word_count = processor.count_words(chunk)
                    chunk_source_name = f"{base_source_name}_{j}"
                    
                    metadata = {
                        "source": chunk_source_name,
                        "grade": grade,
                        "subject": subject,
                        "file_path": file_path,
                        "title_pdf": f"{title_pdf}_{j}",
                        "word_count": chunk_word_count,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "original_word_count": word_count
                    }
                    
                    document = Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                    
                    chunk_documents.append(document)
                    print(f"            📦 Created chunk {j+1}/{len(chunks)} ({chunk_word_count} words)")
                
                # Load all chunks for this file
                if is_first_directory and i == 1:
                    # First file of first directory: create new vector store
                    vector_store.create_vector_store(chunk_documents)
                else:
                    # Add to existing store
                    vector_store.add_documents(chunk_documents)
                
                processed_count += len(chunk_documents)
                print(f"         ✅ Processed {len(chunks)} chunks")
            
        except Exception as e:
            print(f"         ❌ Error processing {filename}: {str(e)}")
            continue
    
    print(f"   ✅ Completed directory: {processed_count} documents processed")
    return processed_count

def process_and_load_directory_by_directory():
    """Process and load each directory individually to minimize memory usage."""
    
    print("🔄 Processing and Loading NCERT Textbooks Directory by Directory")
    print("=" * 60)
    
    # Initialize text processor and vector store
    processor = TextProcessor()
    vector_store = VectorStore(db_type="chroma")
    
    # Find all textbook directories
    textbook_dirs = find_all_textbook_directories()
    
    if not textbook_dirs:
        print("❌ No valid textbook directories found!")
        return False
    
    print(f"📚 Found {len(textbook_dirs)} textbook directories")
    
    # Clean the database first
    print("\n1️⃣ Cleaning existing Chroma database...")
    if not clean_chroma_database():
        print("❌ Failed to clean database")
        return False
    
    total_documents = 0
    stats = defaultdict(int)
    
    print(f"\n🔄 Processing and loading directories one by one...")
    
    for i, dir_info in enumerate(textbook_dirs, 1):
        directory_path = dir_info['path']
        grade, subject = extract_grade_and_subject_from_path(directory_path)
        
        print(f"\n📁 Processing {i}/{len(textbook_dirs)}: {directory_path}")
        print(f"   Grade: {grade or 'Unknown'}, Subject: {subject or 'Unknown'}")
        
        try:
            # Check if this is a large directory that needs special handling
            if is_large_directory(directory_path):
                print(f"   ⚠️  Large directory detected - using file-by-file processing")
                processed_count = process_directory_file_by_file(
                    processor=processor,
                    vector_store=vector_store,
                    directory_path=directory_path,
                    grade=grade,
                    subject=subject,
                    is_first_directory=(i == 1)
                )
            else:
                # Process the directory normally
                documents = processor.process_directory(
                    directory_path=directory_path,
                    grade=grade,
                    subject=subject
                )
                
                if documents:
                    # Load this directory's documents to vector database
                    print(f"   📚 Loading {len(documents)} documents to database...")
                    
                    if i == 1:
                        # First directory: create new vector store
                        vector_store.create_vector_store(documents)
                    else:
                        # Subsequent directories: add to existing store
                        vector_store.add_documents(documents)
                    
                    processed_count = len(documents)
                    print(f"   ✅ Processed and loaded {len(documents)} documents")
                else:
                    print(f"   ⚠️  No documents found in {directory_path}")
                    processed_count = 0
            
            total_documents += processed_count
            stats[f"{grade}_{subject}"] += processed_count
            
        except Exception as e:
            print(f"   ❌ Error processing {directory_path}: {str(e)}")
            continue
    
    print(f"\n📊 Final Summary:")
    print(f"   Total directories processed: {len(textbook_dirs)}")
    print(f"   Total documents loaded: {total_documents}")
    
    print(f"\n📈 Documents by Grade/Subject:")
    for key, count in sorted(stats.items()):
        print(f"   {key}: {count} documents")
    
    return True

def is_large_directory(directory_path):
    """Check if a directory contains large files that might cause memory issues."""
    total_size = 0
    large_file_count = 0
    
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf') and filename.lower() != 'title.pdf':
            file_path = os.path.join(directory_path, filename)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                if file_size > 10 * 1024 * 1024:  # 10MB
                    large_file_count += 1
            except:
                continue
    
    # Consider it large if total size > 50MB or has more than 2 large files
    return total_size > 50 * 1024 * 1024 or large_file_count > 2

def main():
    """Main function to clean and load all NCERT textbooks."""
    print("📚 NCERT Textbooks - Complete Database Load")
    print("=" * 60)
    
    # Use the new directory-by-directory approach to prevent memory issues
    print("\n🔄 Using memory-efficient directory-by-directory processing...")
    
    if process_and_load_directory_by_directory():
        print("\n🎉 Successfully completed full NCERT textbooks database load!")
        print("\n🔍 Now you can run the visualization script:")
        print("   python visualize_vector_db.py")
    else:
        print("\n❌ Failed to complete the database load")
        return

if __name__ == "__main__":
    main()
