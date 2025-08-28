#!/usr/bin/env python3
"""
Clean Chroma database and reload with fresh data using new source naming logic
"""

import os
import shutil
import sys
from text_processor import TextProcessor
from vector_store import VectorStore

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

def process_and_load_data():
    """Process marigold directory and load into fresh Chroma database."""
    
    print("🔄 Processing and Loading Data")
    print("=" * 40)
    
    # Initialize text processor
    processor = TextProcessor()
    
    # Process the marigold directory with new source naming logic
    marigold_dir = "NCERT_Textbooks/class1/english/marigold"
    
    if not os.path.exists(marigold_dir):
        print(f"❌ Directory {marigold_dir} not found!")
        return False
    
    print(f"📁 Processing directory: {marigold_dir}")
    
    # Process documents with new source naming
    documents = processor.process_directory(
        directory_path=marigold_dir,
        grade="class1",
        subject="english"
    )
    
    print(f"✅ Processed {len(documents)} documents with new source naming")
    
    # Show the new source names
    print(f"\n📋 New Source Names:")
    for i, doc in enumerate(documents, 1):
        print(f"   {i}. {doc.metadata['source']} (from {os.path.basename(doc.metadata['file_path'])})")
    
    # Initialize vector store
    vector_store = VectorStore(db_type="chroma")
    
    # Create new vector store
    try:
        vector_store.create_vector_store(documents)
        print("✅ Created new Chroma vector store with documents")
        return True
    except Exception as e:
        print(f"❌ Error creating vector store: {str(e)}")
        return False

def main():
    """Main function to clean and reload the database."""
    print("🧹 Chroma Database Clean and Reload")
    print("=" * 50)
    
    # Step 1: Clean the database
    print("\n1️⃣ Cleaning existing Chroma database...")
    if not clean_chroma_database():
        print("❌ Failed to clean database")
        return
    
    # Step 2: Process and load new data
    print("\n2️⃣ Processing and loading new data...")
    if not process_and_load_data():
        print("❌ Failed to process and load data")
        return
    
    print("\n✅ Successfully cleaned and reloaded Chroma database!")
    print("\n🔍 Now you can run the visualization script:")
    print("   python visualize_vector_db.py")

if __name__ == "__main__":
    main()
