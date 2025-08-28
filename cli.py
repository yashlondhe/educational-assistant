#!/usr/bin/env python3
"""
Command Line Interface for the Educational Assistant
"""

import argparse
import sys
import os
from typing import Optional

from educational_assistant import EducationalAssistant
from config import Config

def setup_assistant(db_type: str = "chroma") -> EducationalAssistant:
    """Initialize the educational assistant."""
    try:
        assistant = EducationalAssistant(db_type=db_type)
        return assistant
    except Exception as e:
        print(f"Error initializing assistant: {e}")
        sys.exit(1)

def setup_database(assistant: EducationalAssistant, textbooks_dir: str) -> bool:
    """Set up the vector database with textbooks."""
    print("Setting up database...")
    result = assistant.setup_database(textbooks_dir)
    
    if result["status"] == "success":
        print(f"✅ Database setup completed successfully!")
        print(f"   - Textbooks processed: {result['textbooks_processed']}")
        print(f"   - Total documents: {result['total_documents']}")
        return True
    else:
        print(f"❌ Database setup failed: {result['message']}")
        return False

def interactive_mode(assistant: EducationalAssistant):
    """Run the assistant in interactive mode."""
    print("\n🎓 Educational Assistant - Interactive Mode")
    print("Type 'quit' or 'exit' to stop")
    print("Type 'info' to see database information")
    print("-" * 50)
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() == 'info':
                info = assistant.get_database_info()
                print(f"\n📊 Database Information:")
                print(f"   Status: {info['status']}")
                if info['status'] == 'initialized':
                    print(f"   Type: {info['db_type']}")
                    print(f"   Documents: {info.get('documents_count', 'Unknown')}")
                    print(f"   Embedding Model: {info['embedding_model']}")
                else:
                    print(f"   Message: {info['message']}")
                continue
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            result = assistant.answer_question(question)
            
            # Display template information
            if "template_info" in result:
                template_info = result["template_info"]
                print(f"\n🔍 TEMPLATE ANALYSIS:")
                print(f"   Question Type: {template_info['question_type']}")
                print(f"   Subject: {template_info['subject']}")
                print(f"   Grade Level: {template_info['grade_level']}")
                print(f"   Complexity: {template_info['complexity']}")
                print(f"   Template Used: {template_info['template_used']}")
                print(f"   Model: {template_info['model']}")
                print(f"   Context Documents: {template_info['context_documents_count']}")
                print(f"   Keywords: {', '.join(template_info['keywords'])}")
                print("-" * 50)
            
            print(f"\n💡 Answer:")
            print(result["answer"])
            
            if result["sources"]:
                print(f"\n📚 Sources: {', '.join(result['sources'])}")
            if result["grades"]:
                print(f"📖 Grades: {', '.join(result['grades'])}")
            if result["subjects"]:
                print(f"📝 Subjects: {', '.join(result['subjects'])}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="AI Educational Assistant using RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up database with textbooks
  python cli.py setup --textbooks-dir ./textbooks
  
  # Run in interactive mode
  python cli.py interactive
  
  # Ask a single question
  python cli.py ask "Explain photosynthesis for Class 6"
  
  # Get database information
  python cli.py info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up the vector database with textbooks')
    setup_parser.add_argument('--textbooks-dir', default=Config.TEXTBOOKS_DIR,
                             help='Directory containing textbook files')
    setup_parser.add_argument('--db-type', choices=['chroma', 'faiss'], default='chroma',
                             help='Type of vector database to use')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Run in interactive mode')
    interactive_parser.add_argument('--db-type', choices=['chroma', 'faiss'], default='chroma',
                                   help='Type of vector database to use')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a single question')
    ask_parser.add_argument('question', help='The question to ask')
    ask_parser.add_argument('--db-type', choices=['chroma', 'faiss'], default='chroma',
                           help='Type of vector database to use')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get database information')
    info_parser.add_argument('--db-type', choices=['chroma', 'faiss'], default='chroma',
                            help='Type of vector database to use')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check for OpenAI API key
    if not Config.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    # Initialize assistant
    db_type = getattr(args, 'db_type', 'chroma')
    assistant = setup_assistant(db_type)
    
    if args.command == 'setup':
        success = setup_database(assistant, args.textbooks_dir)
        sys.exit(0 if success else 1)
    
    elif args.command == 'interactive':
        interactive_mode(assistant)
    
    elif args.command == 'ask':
        try:
            print(f"❓ Question: {args.question}")
            print("🤔 Thinking...")
            result = assistant.answer_question(args.question)
            
            # Display template information
            if "template_info" in result:
                template_info = result["template_info"]
                print(f"\n🔍 TEMPLATE ANALYSIS:")
                print(f"   Question Type: {template_info['question_type']}")
                print(f"   Subject: {template_info['subject']}")
                print(f"   Grade Level: {template_info['grade_level']}")
                print(f"   Complexity: {template_info['complexity']}")
                print(f"   Template Used: {template_info['template_used']}")
                print(f"   Model: {template_info['model']}")
                print(f"   Context Documents: {template_info['context_documents_count']}")
                print(f"   Keywords: {', '.join(template_info['keywords'])}")
                print("-" * 50)
            
            print(f"\n💡 Answer:")
            print(result["answer"])
            
            if result["sources"]:
                print(f"\n📚 Sources: {', '.join(result['sources'])}")
            if result["grades"]:
                print(f"📖 Grades: {', '.join(result['grades'])}")
            if result["subjects"]:
                print(f"📝 Subjects: {', '.join(result['subjects'])}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif args.command == 'info':
        info = assistant.get_database_info()
        print(f"📊 Database Information:")
        print(f"   Status: {info['status']}")
        if info['status'] == 'initialized':
            print(f"   Type: {info['db_type']}")
            print(f"   Documents: {info.get('documents_count', 'Unknown')}")
            print(f"   Embedding Model: {info['embedding_model']}")
        else:
            print(f"   Message: {info['message']}")

if __name__ == "__main__":
    main()
