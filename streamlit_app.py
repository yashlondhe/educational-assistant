import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import uuid
import tempfile
import openai

from educational_assistant import EducationalAssistant
from auth import AuthManager, AuthenticationError
from user_manager import UserManager
from content_manager import ContentManager
from database import Database
from config import Config
from history_manager import HistoryManager

# Page configuration
st.set_page_config(
    page_title="AI Educational Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    .profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    .stButton > button[data-testid="baseButton-secondary"] {
        width: 40px !important;
        height: 40px !important;
        border-radius: 50% !important;
        background-color: #1f77b4 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 14px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0 !important;
        min-height: 40px !important;
    }
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #0d5aa7 !important;
        border-color: #1f77b4 !important;
        color: white !important;
    }
    .stButton > button[data-testid="baseButton-secondary"]:focus {
        background-color: #0d5aa7 !important;
        border-color: #1f77b4 !important;
        color: white !important;
        box-shadow: none !important;
    }
    .profile-dropdown {
        position: relative;
        display: inline-block;
    }
    .dropdown-content {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 8px;
        margin-top: 8px;
        min-width: 160px;
    }
    .dropdown-content .stButton > button {
        width: 100% !important;
        text-align: left !important;
        border-radius: 4px !important;
        margin-bottom: 4px !important;
        background-color: transparent !important;
        color: #333 !important;
        border: none !important;
        font-size: 14px !important;
        padding: 8px 12px !important;
        height: auto !important;
        min-height: auto !important;
    }
    .dropdown-content .stButton > button:hover {
        background-color: #f0f2f6 !important;
        color: #1f77b4 !important;
    }
    .content-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    .step-header {
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .input-mode-container {
        display: flex;
        gap: 10px;
        margin-bottom: 1rem;
        justify-content: center;
    }
    .input-mode-button {
        flex: 1;
        text-align: center;
    }
    .voice-input-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 2px dashed #28a745;
        margin: 1rem 0;
    }
    .transcribed-text-box {
        background-color: #e8f5e8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    .audio-instructions {
        color: #6c757d;
        font-style: italic;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_user_initials(name):
    """Get user initials from full name."""
    if not name:
        return "U"
    
    words = name.strip().split()
    if len(words) == 1:
        return words[0][0].upper()
    elif len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    else:
        return "U"

def transcribe_audio_with_openai(audio_bytes):
    """Convert audio bytes to text using OpenAI Whisper API."""
    if not audio_bytes:
        return ""
    
    try:
        # Create OpenAI client
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # Transcribe using OpenAI Whisper
        with open(tmp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Return the transcribed text
        result = transcript.strip() if hasattr(transcript, 'strip') else str(transcript).strip()
        return result
        
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return ""

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
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = None
    if 'full_conversation_history' not in st.session_state:
        st.session_state.full_conversation_history = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📚 Study Assistant"
    if 'input_mode' not in st.session_state:
        st.session_state.input_mode = "text"  # "text" or "voice"
    if 'transcribed_text' not in st.session_state:
        st.session_state.transcribed_text = ""
    if 'last_audio_hash' not in st.session_state:
        st.session_state.last_audio_hash = None

@st.cache_resource
def initialize_services():
    """Initialize all services."""
    try:
        db = Database()
        auth_manager = AuthManager(db)
        user_manager = UserManager(db)
        content_manager = ContentManager(db)
        assistant = EducationalAssistant()
        history_manager = HistoryManager(db, assistant.llm_interface)
        
        # Initialize content if needed
        content_manager.initialize_content()
        
        return db, auth_manager, user_manager, content_manager, assistant, history_manager
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return None, None, None, None, None, None

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
                        st.session_state.session_id = str(uuid.uuid4())
                        st.session_state.session_start_time = datetime.now()
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
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.session_start_time = datetime.now()
                    st.success("Registration successful! You are now logged in.")
                    st.rerun()
                    
                except AuthenticationError as e:
                    st.error(f"Registration failed: {str(e)}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def main_app(auth_manager: AuthManager, user_manager: UserManager, content_manager: ContentManager, 
             assistant: EducationalAssistant, history_manager: HistoryManager):
    """Display main application interface."""
    user_info = st.session_state.user_info
    
    # Profile header with dropdown
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown('<h1 class="main-header">🎓 AI Educational Assistant</h1>', unsafe_allow_html=True)
    
    with col2:
        # Profile dropdown
        user_initials = get_user_initials(user_info['name'])
        
        # Create a container for the profile dropdown
        profile_container = st.container()
        
        with profile_container:
            # Profile avatar button
            if st.button(user_initials, key="profile_avatar", help=f"Profile: {user_info['name']}"):
                st.session_state.show_profile_dropdown = not st.session_state.get('show_profile_dropdown', False)
            
            # Profile dropdown menu
            if st.session_state.get('show_profile_dropdown', False):
                st.markdown('<div class="dropdown-content">', unsafe_allow_html=True)
                if st.button("👤 Go to Profile", key="goto_profile", use_container_width=True):
                    st.session_state.current_page = "👤 Profile"
                    st.session_state.show_profile_dropdown = False
                    st.rerun()
                
                if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
                    # Save conversation history before logout
                    if st.session_state.full_conversation_history:
                        with st.spinner("Saving conversation history..."):
                            history_manager.save_session_history(
                                user_id=st.session_state.user_id,
                                session_id=st.session_state.session_id,
                                conversations=st.session_state.full_conversation_history,
                                start_time=st.session_state.session_start_time,
                                end_time=datetime.now()
                            )
                    
                    # Clear session state
                    st.session_state.authenticated = False
                    st.session_state.user_id = None
                    st.session_state.user_info = None
                    st.session_state.selected_subject = None
                    st.session_state.selected_textbooks = []
                    st.session_state.chat_history = []
                    st.session_state.full_conversation_history = []
                    st.session_state.session_id = None
                    st.session_state.session_start_time = None
                    st.session_state.current_page = "📚 Study Assistant"
                    st.session_state.show_profile_dropdown = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Selection form in main content area
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.subheader("1️⃣ Class")
        st.info(f"Your class: **{user_info['class_grade'].replace('class', 'Class ')}**")
    
    with col2:
        st.subheader("2️⃣ Select Subject")
        
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
                "Subject",
                subject_names,
                index=default_index,
                key="subject_selector",
                label_visibility="collapsed"
            )
            
            # Find selected subject ID
            selected_subject = next(s for s in subjects if s['subject_name'] == selected_subject_name)
            
            # Save subject selection
            if st.button("💾 Save Subject", use_container_width=True):
                if user_manager.select_subject(st.session_state.user_id, selected_subject['id']):
                    st.session_state.selected_subject = selected_subject
                    st.success("Subject selection saved!")
                    st.rerun()
                else:
                    st.error("Failed to save subject selection")
        else:
            st.warning("No subjects available for your class")
    
    with col3:
        st.subheader("3️⃣ Select Textbooks")
        
        # Textbook selection (only if subject is selected)
        current_selection = user_manager.db.get_user_subject_selection(st.session_state.user_id)
        if current_selection:
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
                
                if st.button("💾 Save Textbooks", use_container_width=True):
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
            st.info("Please select a subject first")
    
    st.markdown("---")
    
    # Validate selections before allowing questions
    validation = user_manager.validate_user_selections(st.session_state.user_id)
    
    if not validation['is_valid']:
        st.markdown("""
        <div style="background-color: #fff3cd; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #ffc107; margin: 2rem 0;">
            <h3 style="color: #856404; margin-bottom: 1rem;">⚠️ Complete Your Setup First</h3>
            <p style="color: #856404; margin-bottom: 0;">Please complete all selections above before you can start asking questions.</p>
        </div>
        """, unsafe_allow_html=True)
        
        for error in validation['errors']:
            st.error(f"• {error}")
        
        # Show example questions anyway
        st.markdown("### 📝 Example Questions (Available After Setup)")
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
        
        # Success message and question input
        st.markdown("""
        <div style="background-color: #d1ecf1; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #17a2b8; margin: 2rem 0;">
            <h3 style="color: #0c5460; margin-bottom: 1rem;">✅ Ready to Learn!</h3>
            <p style="color: #0c5460; margin-bottom: 0;">All selections complete. You can now ask questions about your selected subjects and textbooks.</p>
        </div>
        """, unsafe_allow_html=True)
        

        
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
        
        # Input mode selection (outside form)
        st.markdown("### 💬 Ask Your Question")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Text Input", use_container_width=True):
                st.session_state.input_mode = "text"
                st.session_state.transcribed_text = ""
        with col2:
            if st.button("🎤 Voice Input", use_container_width=True):
                st.session_state.input_mode = "voice"
        
        # Voice input processing (outside form for immediate transcription)
        if st.session_state.input_mode == "voice":
            st.info("🎤 **Voice Input Mode** - Record your question below")
            
            # Audio input with instructions
            st.markdown('<p class="audio-instructions">Click the audio recorder below to start recording your question</p>', unsafe_allow_html=True)
            audio_data = st.audio_input("Record your question:")
            
            if audio_data is not None:
                # Show audio player
                st.audio(audio_data)
                
                # Transcribe audio only if we haven't transcribed this audio yet
                audio_bytes = audio_data.getvalue()
                current_audio_hash = str(hash(audio_bytes))
                
                if 'last_audio_hash' not in st.session_state or st.session_state.last_audio_hash != current_audio_hash:
                    # New audio, transcribe it immediately
                    with st.spinner("🔄 Converting speech to text..."):
                        transcribed = transcribe_audio_with_openai(audio_bytes)
                    
                    if transcribed:
                        st.session_state.transcribed_text = transcribed
                        st.session_state.last_audio_hash = current_audio_hash
                        st.success("✅ Audio transcribed successfully!")
                        # Force a rerun to update the UI
                        st.rerun()
                    else:
                        st.error("❌ Could not transcribe audio. Please try again or switch to text input.")
                else:
                    # Same audio, use previous transcription
                    if st.session_state.transcribed_text:
                        st.success("✅ Using previous transcription")
            
            # Show transcription result if available
            if st.session_state.transcribed_text:
                st.markdown(f'<div class="transcribed-text-box">📝 <strong>Transcribed:</strong> {st.session_state.transcribed_text}</div>', 
                           unsafe_allow_html=True)
        
        # Question form (now only for final submission)
        with st.form("question_form", clear_on_submit=True):
            # Show current mode
            if st.session_state.input_mode == "text":
                st.info("📝 **Text Input Mode** - Type your question below")
                question = st.text_area(
                    "Your Question",
                    placeholder=f"Ask any question about {summary['subject']}...",
                    height=100,
                    value=st.session_state.transcribed_text
                )
            
            else:  # voice mode
                # Text editing section for voice mode
                st.markdown('<div class="voice-input-section">', unsafe_allow_html=True)
                
                if st.session_state.transcribed_text:
                    # Show editable text area with transcribed content
                    col_text, col_clear = st.columns([4, 1])
                    with col_text:
                        st.markdown("**Review and edit your question before submitting:**")
                    with col_clear:
                        if st.form_submit_button("🗑️ Clear", help="Clear transcribed text"):
                            st.session_state.transcribed_text = ""
                            st.session_state.last_audio_hash = None
                            st.rerun()
                    
                    question = st.text_area(
                        "Edit your question:",
                        value=st.session_state.transcribed_text,
                        height=100,
                        help="You can edit the transcribed text before submitting your question.",
                        key="voice_editable_text"
                    )
                    
                else:
                    # Show disabled text area when no transcription
                    st.markdown("**Record audio above to enable text editing**")
                    question = st.text_area(
                        "Your transcribed question will appear here:",
                        value="",
                        height=100,
                        placeholder="Record audio above to see transcribed text here...",
                        disabled=True,
                        help="This text box will become editable after you record and transcribe audio.",
                        key="voice_disabled_text"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Submit button (same for both modes)
            col1, col2 = st.columns([1, 5])
            with col1:
                submit_button = st.form_submit_button("Ask", type="primary", use_container_width=True)
        
        if submit_button and question:
            with st.spinner("🤔 Thinking..."):
                try:
                    # Check if we need historical context
                    should_include_history, reason = history_manager.should_include_history(
                        question, st.session_state.user_id
                    )
                    
                    # Get historical context if needed
                    historical_context = None
                    if should_include_history:
                        st.info(f"📚 Including context from previous sessions: {reason}")
                        history_summaries = history_manager.get_recent_history(
                            st.session_state.user_id, limit=5
                        )
                        if history_summaries:
                            historical_context = history_manager.format_history_context(history_summaries)
                    
                    # Include current session context
                    current_session_context = []
                    if st.session_state.chat_history:
                        # Include last 3 Q&A from current session
                        for chat in st.session_state.chat_history[-3:]:
                            current_session_context.append({
                                'question': chat['question'],
                                'answer': chat['answer'][:200] + '...'  # Truncate for context
                            })
                    
                    # Get answer with user context
                    result = assistant.answer_question(
                        question=question,
                        user_id=st.session_state.user_id,
                        historical_context=historical_context,
                        current_session_context=current_session_context
                    )
                    
                    # Add to chat history
                    conversation_entry = {
                        'question': question,
                        'answer': result['answer'],
                        'timestamp': datetime.now()
                    }
                    
                    st.session_state.chat_history.append(conversation_entry)
                    st.session_state.full_conversation_history.append(conversation_entry)
                    
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

def profile_page(auth_manager: AuthManager, user_manager: UserManager, history_manager: HistoryManager):
    """Display user profile page."""
    user_info = st.session_state.user_info
    
    # Profile header with dropdown (same as main app)
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown('<h1 class="main-header">👤 User Profile</h1>', unsafe_allow_html=True)
    
    with col2:
        # Profile dropdown
        user_initials = get_user_initials(user_info['name'])
        
        # Create a container for the profile dropdown
        profile_container = st.container()
        
        with profile_container:
            # Profile avatar button
            if st.button(user_initials, key="profile_avatar_profile", help=f"Profile: {user_info['name']}"):
                st.session_state.show_profile_dropdown = not st.session_state.get('show_profile_dropdown', False)
            
            # Profile dropdown menu
            if st.session_state.get('show_profile_dropdown', False):
                st.markdown('<div class="dropdown-content">', unsafe_allow_html=True)
                if st.button("📚 Go to Study Assistant", key="goto_study", use_container_width=True):
                    st.session_state.current_page = "📚 Study Assistant"
                    st.session_state.show_profile_dropdown = False
                    st.rerun()
                
                if st.button("🚪 Logout", key="logout_btn_profile", use_container_width=True):
                    # Save conversation history before logout
                    if st.session_state.full_conversation_history:
                        with st.spinner("Saving conversation history..."):
                            history_manager.save_session_history(
                                user_id=st.session_state.user_id,
                                session_id=st.session_state.session_id,
                                conversations=st.session_state.full_conversation_history,
                                start_time=st.session_state.session_start_time,
                                end_time=datetime.now()
                            )
                    
                    # Clear session state
                    st.session_state.authenticated = False
                    st.session_state.user_id = None
                    st.session_state.user_info = None
                    st.session_state.selected_subject = None
                    st.session_state.selected_textbooks = []
                    st.session_state.chat_history = []
                    st.session_state.full_conversation_history = []
                    st.session_state.session_id = None
                    st.session_state.session_start_time = None
                    st.session_state.current_page = "📚 Study Assistant"
                    st.session_state.show_profile_dropdown = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    
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
    db, auth_manager, user_manager, content_manager, assistant, history_manager = initialize_services()
    
    if not all([db, auth_manager, user_manager, content_manager, assistant, history_manager]):
        st.error("Failed to initialize application. Please check the logs.")
        return
    
    # Authentication check
    if not st.session_state.authenticated:
        login_page(auth_manager)
    else:
        # Display current page based on session state
        if st.session_state.current_page == "📚 Study Assistant":
            main_app(auth_manager, user_manager, content_manager, assistant, history_manager)
        elif st.session_state.current_page == "👤 Profile":
            profile_page(auth_manager, user_manager, history_manager)

if __name__ == "__main__":
    main()
