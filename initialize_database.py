#!/usr/bin/env python3
"""
Initialize the database with NCERT content structure.
Run this script once to populate the class-subject-textbook mappings.
"""

import logging
from content_manager import ContentManager
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize the database with NCERT content."""
    print("=" * 60)
    print("Educational Assistant - Database Initialization")
    print("=" * 60)
    
    # Initialize database and content manager
    db = Database()
    content_manager = ContentManager(db)
    
    print("\nInitializing database with NCERT content...")
    
    # Initialize content
    result = content_manager.initialize_content()
    
    if result['success']:
        print("\n✅ Database initialized successfully!")
        
        stats = result.get('stats', {})
        print(f"\nSummary:")
        print(f"  Classes added: {stats.get('classes_added', 0)}")
        print(f"  Subjects added: {stats.get('subjects_added', 0)}")
        print(f"  Textbooks added: {stats.get('textbooks_added', 0)}")
        
        if stats.get('errors'):
            print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Show content summary
        print("\n📚 Content Summary:")
        summary = content_manager.get_content_summary()
        
        for class_info in summary['classes']:
            print(f"\n{class_info['display_name']}:")
            for subject in class_info['subjects']:
                print(f"  - {subject['name']} ({subject['textbook_count']} textbooks)")
        
        print(f"\nTotal: {len(summary['classes'])} classes, {summary['total_subjects']} subjects, {summary['total_textbooks']} textbooks")
    
    else:
        print(f"\n❌ Database initialization failed: {result.get('error', 'Unknown error')}")
        if result.get('stats', {}).get('errors'):
            print("\nErrors:")
            for error in result['stats']['errors']:
                print(f"  - {error}")

if __name__ == "__main__":
    main()
