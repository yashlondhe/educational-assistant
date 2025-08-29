import streamlit as st
import os
from pathlib import Path
from datetime import datetime

from educational_assistant import EducationalAssistant
from auth import AuthManager, AuthenticationError
from user_manager import UserManager
from content_manager import ContentManager
from database import Database
from config import Config

# Page configuration
st.set_page_config(
    page_title="AI Educational Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .answer-box {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .user-info {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .selection-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'selected_subject' not in st.session_state:
        st.session_state.selected_subject = None
    if 'selected_textbooks' not in st.session_state:
        st.session_state.selected_textbooks = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

@st.cache_resource
def initialize_services():
    """Initialize all services."""
    try:
        db = Database()
        auth_manager = AuthManager(db)
        user_manager = UserManager(db)
        content_manager = ContentManager(db)
        assistant = EducationalAssistant()
        
        # Initialize content if needed
        content_manager.initialize_content()
        
        return db, auth_manager, user_manager, content_manager, assistant
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return None, None, None, None, None

def login_page(auth_manager: AuthManager):
    """Display login/registration page."""
    st.markdown('<h1 class="main-header">🎓 AI Educational Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Welcome! Please login or register to continue")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary"):
                if email and password:
                    user_info = auth_manager.login(email, password)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_info['user_id']
                        st.session_state.user_info = user_info
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Register New Account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                reg_email = st.text_input("Email*", placeholder="your.email@example.com", key="reg_email")
                reg_password = st.text_input("Password*", type="password", help="Minimum 6 characters", key="reg_password")
                reg_name = st.text_input("Full Name*", placeholder="John Doe", key="reg_name")
            
            with col2:
                classes = [f"Class {i}" for i in range(1, 11)]
                reg_class = st.selectbox("Class*", classes, key="reg_class")
                reg_class_value = f"class{classes.index(reg_class) + 1}"
                
                reg_dob = st.date_input("Date of Birth", min_value=datetime(1990, 1, 1), max_value=datetime.now(), key="reg_dob")
                reg_phone = st.text_input("Phone Number", placeholder="9876543210", key="reg_phone")
            
            st.markdown("*Required fields")
            
            if st.form_submit_button("Register", type="primary"):
                try:
                    user_info = auth_manager.register_user(
                        email=reg_email,
                        password=reg_password,
                        name=reg_name,
                        class_grade=reg_class_value,
                        date_of_birth=str(reg_dob) if reg_dob else None,
                        phone_number=reg_phone
                    )
                    
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_info['user_id']
                    st.session_state.user_info = user_info
                    st.success("Registration successful! You are now logged in.")
                    st.rerun()
                    
                except AuthenticationError as e:
                    st.error(f"Registration failed: {str(e)}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def main_app(auth_manager: AuthManager, user_manager: UserManager, content_manager: ContentManager, assistant: EducationalAssistant):
    """Display main application interface."""
    user_info = st.session_state.user_info
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-info">
            <h4>👤 {user_info['name']}</h4>
            <p>📧 {user_info['email']}</p>
            <p>🎓 {user_info['class_grade'].replace('class', 'Class ')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.selected_subject = None
            st.session_state.selected_textbooks = []
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # Subject and Textbook Selection
        st.subheader("📚 Content Selection")
        
        # Get available subjects for user's class
        subjects = user_manager.get_available_subjects(st.session_state.user_id)
        
        if subjects:
            # Subject selection
            subject_names = [s['subject_name'] for s in subjects]
            current_subject = user_manager.db.get_user_subject_selection(st.session_state.user_id)
            
            if current_subject:
                default_index = next((i for i, s in enumerate(subjects) if s['id'] == current_subject['subject_id']), 0)
            else:
                default_index = 0
            
            selected_subject_name = st.selectbox(
                "Select Subject",
                subject_names,
                index=default_index,
                key="subject_selector"
            )
            
            # Find selected subject ID
            selected_subject = next(s for s in subjects if s['subject_name'] == selected_subject_name)
            
            # Save subject selection
            if st.button("Save Subject Selection", use_container_width=True):
                if user_manager.select_subject(st.session_state.user_id, selected_subject['id']):
                    st.session_state.selected_subject = selected_subject
                    st.success("Subject selection saved!")
                    st.rerun()
                else:
                    st.error("Failed to save subject selection")
            
            # Textbook selection (only if subject is selected)
            current_selection = user_manager.db.get_user_subject_selection(st.session_state.user_id)
            if current_selection:
                st.divider()
                st.subheader("📖 Select Textbooks")
                
                available_textbooks = user_manager.get_available_textbooks(st.session_state.user_id)
                
                if available_textbooks:
                    # Create checkboxes for each textbook
                    selected_ids = []
                    for textbook in available_textbooks:
                        if st.checkbox(
                            textbook['book_name'],
                            value=textbook['is_selected'],
                            key=f"textbook_{textbook['id']}"
                        ):
                            selected_ids.append(textbook['id'])
                    
                    if st.button("Save Textbook Selection", use_container_width=True):
                        if selected_ids:
                            if user_manager.select_textbooks(st.session_state.user_id, selected_ids):
                                st.success("Textbook selection saved!")
                                st.rerun()
                            else:
                                st.error("Failed to save textbook selection")
                        else:
                            st.error("Please select at least one textbook")
                else:
                    st.info("No textbooks available for this subject")
        else:
            st.warning("No subjects available for your class")
        
        # Show current selection summary
        st.divider()
        st.subheader("📋 Current Selection")
        summary = user_manager.get_selection_summary(st.session_state.user_id)
        
        if summary['subject']:
            st.write(f"**Subject:** {summary['subject']}")
            if summary['textbooks']:
                st.write(f"**Textbooks:** {summary['textbook_count']}")
                for book in summary['textbooks']:
                    st.write(f"  - {book}")
            else:
                st.warning("No textbooks selected")
        else:
            st.warning("No subject selected")
    
    # Main content area
    st.markdown('<h1 class="main-header">🎓 AI Educational Assistant</h1>', unsafe_allow_html=True)
    
    # Validate selections before allowing questions
    validation = user_manager.validate_user_selections(st.session_state.user_id)
    
    if not validation['is_valid']:
        st.error("⚠️ Please complete your selection before asking questions:")
        for error in validation['errors']:
            st.error(f"  • {error}")
        
        # Show example questions anyway
        st.subheader("📝 Example Questions")
        example_questions = [
            "What is photosynthesis?",
            "Explain the water cycle",
            "What are prime numbers?",
            "How do plants make food?",
            "What is gravity?"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(example_questions):
            with cols[i % 2]:
                st.info(f"💡 {question}")
    else:
        # Show warnings if any
        if validation['warnings']:
            for warning in validation['warnings']:
                st.warning(f"⚠️ {warning}")
        
        # Question input
        st.subheader("Ask Your Question")
        
        # Example questions based on selected subject
        with st.expander("💡 Example Questions"):
            summary = user_manager.get_selection_summary(st.session_state.user_id)
            subject = summary['subject']
            
            if subject:
                if 'math' in subject.lower():
                    examples = [
                        "What are prime numbers?",
                        "How do I solve linear equations?",
                        "Explain fractions with examples",
                        "What is the Pythagorean theorem?"
                    ]
                elif 'science' in subject.lower():
                    examples = [
                        "What is photosynthesis?",
                        "How does digestion work?",
                        "Explain the water cycle",
                        "What are the states of matter?"
                    ]
                elif 'english' in subject.lower():
                    examples = [
                        "What are nouns and pronouns?",
                        "Explain the parts of speech",
                        "How do I write a good paragraph?",
                        "What is the difference between active and passive voice?"
                    ]
                else:
                    examples = [
                        f"Explain a key concept from {subject}",
                        f"What are the important topics in {subject}?",
                        f"Give me an example from {subject}",
                        f"Help me understand {subject} better"
                    ]
                
                for example in examples:
                    st.write(f"• {example}")
        
        # Question form
        with st.form("question_form", clear_on_submit=True):
            question = st.text_area(
                "Your Question",
                placeholder=f"Ask any question about {summary['subject']}...",
                height=100
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                submit_button = st.form_submit_button("Ask", type="primary", use_container_width=True)
        
        if submit_button and question:
            with st.spinner("🤔 Thinking..."):
                try:
                    # Get answer with user context
                    result = assistant.answer_question(
                        question=question,
                        user_id=st.session_state.user_id
                    )
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'question': question,
                        'answer': result['answer'],
                        'timestamp': datetime.now()
                    })
                    
                    # Display answer
                    st.subheader("Answer")
                    st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)
                    
                    # Show metadata
                    with st.expander("📊 Answer Details"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Model:** {result['model_used']}")
                            st.write(f"**Documents Used:** {result['context_documents_count']}")
                        
                        with col2:
                            if 'template_info' in result:
                                st.write(f"**Question Type:** {result['template_info']['question_type']}")
                                st.write(f"**Detected Subject:** {result['template_info']['subject']}")
                        
                        if result['sources']:
                            st.write("**Sources:**")
                            for source in result['sources']:
                                st.write(f"  • {source}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Chat history
        if st.session_state.chat_history:
            st.divider()
            st.subheader("💬 Chat History")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
                with st.expander(f"Q: {chat['question'][:100]}...", expanded=(i==0)):
                    st.write(f"**Question:** {chat['question']}")
                    st.write(f"**Answer:** {chat['answer']}")
                    st.caption(f"Asked at: {chat['timestamp'].strftime('%Y-%m-%d %H:%M')}")

def profile_page(auth_manager: AuthManager, user_manager: UserManager):
    """Display user profile page."""
    st.markdown('<h1 class="main-header">👤 User Profile</h1>', unsafe_allow_html=True)
    
    user_info = auth_manager.get_user_info(st.session_state.user_id)
    
    if not user_info:
        st.error("Failed to load user profile")
        return
    
    tab1, tab2 = st.tabs(["View Profile", "Edit Profile"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            st.write(f"**Name:** {user_info['name']}")
            st.write(f"**Email:** {user_info['email']}")
            st.write(f"**Class:** {user_info['class_grade'].replace('class', 'Class ')}")
        
        with col2:
            st.subheader("Additional Details")
            st.write(f"**Date of Birth:** {user_info['date_of_birth'] or 'Not provided'}")
            st.write(f"**Phone:** {user_info['phone_number'] or 'Not provided'}")
            st.write(f"**Member Since:** {user_info['created_at'][:10]}")
            st.write(f"**Last Login:** {user_info['last_login'] or 'N/A'}")
    
    with tab2:
        st.subheader("Edit Profile")
        
        with st.form("edit_profile_form"):
            name = st.text_input("Full Name", value=user_info['name'])
            
            classes = [f"Class {i}" for i in range(1, 11)]
            current_class_index = int(user_info['class_grade'].replace('class', '')) - 1
            selected_class = st.selectbox("Class", classes, index=current_class_index)
            class_value = f"class{classes.index(selected_class) + 1}"
            
            dob = st.date_input(
                "Date of Birth",
                value=datetime.strptime(user_info['date_of_birth'], '%Y-%m-%d') if user_info['date_of_birth'] else None,
                min_value=datetime(1990, 1, 1),
                max_value=datetime.now()
            )
            
            phone = st.text_input("Phone Number", value=user_info['phone_number'] or '')
            
            if st.form_submit_button("Update Profile", type="primary"):
                try:
                    success = auth_manager.update_profile(
                        user_id=st.session_state.user_id,
                        name=name,
                        class_grade=class_value,
                        date_of_birth=str(dob) if dob else None,
                        phone_number=phone
                    )
                    
                    if success:
                        st.success("Profile updated successfully!")
                        # Update session state
                        st.session_state.user_info['name'] = name
                        st.session_state.user_info['class_grade'] = class_value
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
                
                except AuthenticationError as e:
                    st.error(f"Update failed: {str(e)}")

# Main app logic
def main():
    init_session_state()
    
    # Initialize services
    db, auth_manager, user_manager, content_manager, assistant = initialize_services()
    
    if not all([db, auth_manager, user_manager, content_manager, assistant]):
        st.error("Failed to initialize application. Please check the logs.")
        return
    
    # Authentication check
    if not st.session_state.authenticated:
        login_page(auth_manager)
    else:
        # Create navigation
        pages = {
            "📚 Study Assistant": lambda: main_app(auth_manager, user_manager, content_manager, assistant),
            "👤 Profile": lambda: profile_page(auth_manager, user_manager)
        }
        
        # Add navigation to sidebar
        with st.sidebar:
            st.title("Navigation")
            selection = st.radio("Go to", list(pages.keys()))
        
        # Display selected page
        pages[selection]()

if __name__ == "__main__":
    main()
