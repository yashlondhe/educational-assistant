#!/usr/bin/env python3
"""
Test script to verify the new user authentication and content selection system.
"""

import os
from database import Database
from auth import AuthManager, AuthenticationError
from user_manager import UserManager
from content_manager import ContentManager
from educational_assistant import EducationalAssistant

def test_system():
    """Test the complete system."""
    print("=" * 60)
    print("Educational Assistant - System Test")
    print("=" * 60)
    
    # Initialize components
    db = Database()
    auth_manager = AuthManager(db)
    user_manager = UserManager(db)
    content_manager = ContentManager(db)
    assistant = EducationalAssistant()
    
    # 1. Initialize content
    print("\n1. Testing Content Initialization...")
    result = content_manager.initialize_content()
    if result['success']:
        print("✅ Content initialized successfully")
        summary = content_manager.get_content_summary()
        print(f"   - Classes: {len(summary['classes'])}")
        print(f"   - Total subjects: {summary['total_subjects']}")
        print(f"   - Total textbooks: {summary['total_textbooks']}")
    else:
        print("❌ Content initialization failed")
        return
    
    # 2. Test user registration
    print("\n2. Testing User Registration...")
    test_email = "test@example.com"
    test_password = "test123"
    
    # Delete test user if exists
    existing_user = db.get_user_by_email(test_email)
    if existing_user:
        db.execute_delete("DELETE FROM user_profiles WHERE user_id = ?", (existing_user['id'],))
        db.execute_delete("DELETE FROM users WHERE id = ?", (existing_user['id'],))
        print("   - Cleaned up existing test user")
    
    try:
        user_info = auth_manager.register_user(
            email=test_email,
            password=test_password,
            name="Test User",
            class_grade="class5",
            phone_number="9876543210"
        )
        print(f"✅ User registered: {user_info['name']} (ID: {user_info['user_id']})")
    except AuthenticationError as e:
        print(f"❌ Registration failed: {e}")
        return
    
    user_id = user_info['user_id']
    
    # 3. Test login
    print("\n3. Testing User Login...")
    login_info = auth_manager.login(test_email, test_password)
    if login_info:
        print(f"✅ Login successful: {login_info['name']}")
    else:
        print("❌ Login failed")
        return
    
    # 4. Test getting available subjects
    print("\n4. Testing Subject Retrieval...")
    subjects = user_manager.get_available_subjects(user_id)
    if subjects:
        print(f"✅ Found {len(subjects)} subjects for {user_info['class_grade']}:")
        for subj in subjects:
            print(f"   - {subj['subject_name']} (ID: {subj['id']})")
    else:
        print("❌ No subjects found")
        return
    
    # 5. Test subject selection
    print("\n5. Testing Subject Selection...")
    if subjects:
        selected_subject = subjects[0]  # Select first subject
        success = user_manager.select_subject(user_id, selected_subject['id'])
        if success:
            print(f"✅ Selected subject: {selected_subject['subject_name']}")
        else:
            print("❌ Subject selection failed")
            return
    
    # 6. Test textbook retrieval
    print("\n6. Testing Textbook Retrieval...")
    textbooks = user_manager.get_available_textbooks(user_id)
    if textbooks:
        print(f"✅ Found {len(textbooks)} textbooks:")
        for book in textbooks:
            print(f"   - {book['book_name']} (ID: {book['id']})")
    else:
        print("❌ No textbooks found")
        return
    
    # 7. Test textbook selection
    print("\n7. Testing Textbook Selection...")
    if textbooks:
        # Select first two textbooks or all if less than 2
        selected_ids = [book['id'] for book in textbooks[:min(2, len(textbooks))]]
        success = user_manager.select_textbooks(user_id, selected_ids)
        if success:
            print(f"✅ Selected {len(selected_ids)} textbooks")
        else:
            print("❌ Textbook selection failed")
            return
    
    # 8. Test selection validation
    print("\n8. Testing Selection Validation...")
    validation = user_manager.validate_user_selections(user_id)
    if validation['is_valid']:
        print("✅ User selections are valid")
    else:
        print("❌ User selections are invalid:")
        for error in validation['errors']:
            print(f"   - {error}")
    
    # 9. Test selection summary
    print("\n9. Testing Selection Summary...")
    summary = user_manager.get_selection_summary(user_id)
    print(f"✅ Selection Summary:")
    print(f"   - Class: {summary['class']}")
    print(f"   - Subject: {summary['subject']}")
    print(f"   - Textbooks: {summary['textbook_count']}")
    for book in summary['textbooks']:
        print(f"     • {book}")
    
    # 10. Test question answering with user context
    print("\n10. Testing Question Answering...")
    test_question = "What is photosynthesis?"
    
    print(f"   Question: {test_question}")
    print(f"   User: {user_info['name']} ({summary['class']})")
    print(f"   Subject: {summary['subject']}")
    
    try:
        # First check if vector store exists
        if assistant.vector_store.vector_store is None:
            assistant.vector_store.load_existing_vector_store()
        
        if assistant.vector_store.vector_store is None:
            print("⚠️  No vector store found. Please run load_all_ncert_textbooks.py first")
        else:
            result = assistant.answer_question(
                question=test_question,
                user_id=user_id
            )
            print("✅ Answer generated successfully")
            print(f"   Preview: {result['answer'][:200]}...")
            print(f"   Context documents: {result['context_documents_count']}")
    except Exception as e:
        print(f"❌ Question answering failed: {e}")
    
    # 11. Test profile update
    print("\n11. Testing Profile Update...")
    try:
        success = auth_manager.update_profile(
            user_id=user_id,
            name="Updated Test User",
            phone_number="9999999999"
        )
        if success:
            print("✅ Profile updated successfully")
            updated_info = auth_manager.get_user_info(user_id)
            print(f"   - Name: {updated_info['name']}")
            print(f"   - Phone: {updated_info['phone_number']}")
        else:
            print("❌ Profile update failed")
    except AuthenticationError as e:
        print(f"❌ Profile update error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_system()
