import streamlit as st
import os
import tempfile
from pathlib import Path
import time

from educational_assistant import EducationalAssistant
from config import Config

# Page configuration
st.set_page_config(
    page_title="AI Educational Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .source-box {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_assistant():
    """Initialize the educational assistant with caching."""
    try:
        assistant = EducationalAssistant()
        return assistant
    except Exception as e:
        st.error(f"Failed to initialize assistant: {e}")
        return None

def upload_textbooks():
    """Handle textbook uploads."""
    st.subheader("📚 Upload Textbooks")
    
    uploaded_files = st.file_uploader(
        "Choose textbook files (PDF or TXT)",
        type=['pdf', 'txt'],
        accept_multiple_files=True,
        help="Upload your textbook files. The system will automatically extract grade and subject from filenames."
    )
    
    if uploaded_files:
        st.write(f"📁 {len(uploaded_files)} files selected")
        
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            for uploaded_file in uploaded_files:
                # Save uploaded file to temporary directory
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)
            
            # Process uploaded files
            if st.button("🚀 Process and Setup Database", type="primary"):
                with st.spinner("Processing textbooks..."):
                    try:
                        assistant = initialize_assistant()
                        if assistant:
                            # Process each file individually
                            all_documents = []
                            progress_bar = st.progress(0)
                            
                            for i, file_path in enumerate(file_paths):
                                st.write(f"Processing {os.path.basename(file_path)}...")
                                
                                # Extract metadata from filename
                                filename = os.path.basename(file_path)
                                grade, subject = assistant._extract_metadata_from_filename(filename)
                                
                                # Process the file
                                documents = assistant.text_processor.process_textbook(
                                    file_path=file_path,
                                    grade=grade,
                                    subject=subject
                                )
                                all_documents.extend(documents)
                                
                                progress_bar.progress((i + 1) / len(file_paths))
                            
                            # Create vector store
                            st.write("Creating embeddings and storing in database...")
                            assistant.create_embeddings(all_documents)
                            
                            st.success(f"✅ Database setup completed!")
                            st.info(f"📊 Processed {len(uploaded_files)} files into {len(all_documents)} document chunks")
                            
                            # Clear cache to refresh assistant state
                            st.cache_resource.clear()
                            
                    except Exception as e:
                        st.error(f"❌ Error processing files: {e}")

def ask_questions(question=None):
    """Main question-answering interface."""
    st.subheader("❓ Ask Questions")
    
    assistant = initialize_assistant()
    if not assistant:
        st.error("Assistant not initialized. Please upload textbooks first.")
        return
    
    # Check database status
    db_info = assistant.get_database_info()
    
    if db_info["status"] != "initialized":
        st.warning("⚠️ No database found. Please upload and process textbooks first.")
        return
    
    # Display database info
    with st.expander("📊 Database Information"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", db_info["status"])
        with col2:
            st.metric("Documents", db_info.get("documents_count", "Unknown"))
        with col3:
            st.metric("Type", db_info["db_type"])
    
    # Question input (only if not provided)
    if question is None:
        question = st.text_area(
            "Enter your question:",
            placeholder="e.g., Explain photosynthesis for Class 6",
            height=100
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            k_results = st.slider("Number of context documents", 1, 5, 2)
            st.caption("⚠️ Higher values may exceed token limits")
        with col2:
            model_choice = st.selectbox(
                "LLM Model",
                ["gpt-4o-mini", "gpt-4", ],
                index=0
            )
            st.caption("💡 GPT-4.1-mini has higher rate limits")
    
    # Ask question
    if st.button("🤔 Ask Question", type="primary") and question:
        with st.spinner("Thinking..."):
            try:
                # Debug: Log the question and parameters
                st.info(f"🔍 Debug: Question: '{question}' | Model: {model_choice} | Context docs: {k_results}")
                
                # Update model if different
                if model_choice != assistant.llm_interface.model_name:
                    st.info(f"🔄 Switching model from {assistant.llm_interface.model_name} to {model_choice}")
                    assistant.llm_interface.model_name = model_choice
                    assistant.llm_interface.llm = assistant.llm_interface.llm.__class__(
                        model=model_choice,
                        temperature=assistant.llm_interface.temperature,
                        max_tokens=assistant.llm_interface.max_tokens,
                        openai_api_key=Config.OPENAI_API_KEY
                    )
                
                # Debug: Log before calling answer_question
                st.info("🚀 Calling assistant.answer_question()...")
                
                # Create a placeholder for template analysis
                template_placeholder = st.empty()
                
                result = assistant.answer_question(question, k=k_results)
                
                # Debug: Log the result
                st.info(f"✅ Received result: {type(result)} | Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                if isinstance(result, dict) and 'answer' in result:
                    st.info(f"📝 Answer length: {len(result['answer'])} characters")
                else:
                    st.error(f"❌ Unexpected result format: {result}")
                
                # Display template information
                if isinstance(result, dict) and 'template_info' in result:
                    template_info = result['template_info']
                    st.markdown("### 🔍 Template Analysis")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Question Type:** {template_info['question_type']}")
                        st.info(f"**Subject:** {template_info['subject']}")
                        st.info(f"**Grade Level:** {template_info['grade_level']}")
                        st.info(f"**Complexity:** {template_info['complexity']}")
                    with col2:
                        st.info(f"**Template Used:** {template_info['template_used']}")
                        st.info(f"**Model:** {template_info['model']}")
                        st.info(f"**Context Docs:** {template_info['context_documents_count']}")
                        st.info(f"**Keywords:** {', '.join(template_info['keywords'])}")
                    st.markdown("---")
                
                # Display answer
                st.markdown("### 💡 Answer")
                
                # Debug: Show raw answer for troubleshooting
                if st.checkbox("🔍 Show debug info"):
                    st.json(result)
                
                if result["answer"]:
                    st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)
                else:
                    st.error("❌ No answer received from OpenAI")
                    st.info("This might be due to an API error or empty response")
                
                # Display metadata
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if result["sources"]:
                        st.markdown("**📚 Sources:**")
                        for source in result["sources"]:
                            st.markdown(f'<div class="source-box">{source}</div>', unsafe_allow_html=True)
                
                with col2:
                    if result["grades"]:
                        st.markdown("**📖 Grades:**")
                        st.write(", ".join(result["grades"]))
                
                with col3:
                    if result["subjects"]:
                        st.markdown("**📝 Subjects:**")
                        st.write(", ".join(result["subjects"]))
                
                with col4:
                    if "question_analysis" in result:
                        analysis = result["question_analysis"]
                        st.markdown("**🔍 Analysis:**")
                        st.write(f"Type: {analysis['type']}")
                        st.write(f"Subject: {analysis['subject']}")
                        st.write(f"Grade: {analysis['grade_level']}")
                        st.write(f"Complexity: {analysis['complexity']}")
                
                # Show context documents (expandable)
                if result["context_documents_count"] > 0:
                    with st.expander(f"🔍 View Context Documents ({result['context_documents_count']} documents)"):
                        context_docs = assistant.retrieve_context(question, k=k_results)
                        for i, doc in enumerate(context_docs, 1):
                            st.markdown(f"**Document {i}:**")
                            st.markdown(f"*Source: {doc.metadata.get('source', 'Unknown')} | Grade: {doc.metadata.get('grade', 'Not specified')}*")
                            st.text_area(f"Content {i}", doc.page_content, height=100, key=f"doc_{i}")
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ Error: {error_msg}")
                
                # Specific error handling
                if "429" in error_msg and "rate_limit" in error_msg:
                    st.error("❌ Rate limit exceeded! Try:")
                    st.markdown("""
                    - **Reduce context documents** (use 1-2 instead of 5)
                    - **Use gpt-4o-mini** instead of gpt-4
                    - **Wait a minute** and try again
                    - **Ask a shorter question**
                    """)
                elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                    st.error("❌ Invalid model name! Available models:")
                    st.markdown("""
                    - **gpt-4o-mini** (recommended)
                    - **gpt-4** 
                    - **gpt-3.5-turbo**
                    """)
                elif "api key" in error_msg.lower():
                    st.error("❌ API key issue! Check your .env file")
                else:
                    st.error(f"❌ Unexpected error: {e}")
                    st.info("🔍 Check the terminal logs for more details")

def example_questions():
    """Show example questions."""
    st.subheader("💡 Example Questions")
    
    examples = [
        "Explain photosynthesis for Class 6",
        "What are the basic properties of matter?",
        "How do plants make their own food?",
        "Explain the water cycle for Class 5",
        "What are the different types of triangles?",
        "How does the digestive system work?",
        "Explain the concept of gravity for Class 7",
        "What are the main parts of a plant cell?"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}"):
                st.session_state.example_question = example
                st.rerun()

def main():
    """Main application."""
    # Header
    st.markdown('<h1 class="main-header">🎓 AI Educational Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Powered by RAG (Retrieval Augmented Generation)</p>', unsafe_allow_html=True)
    
    # Check for API key
    if not Config.OPENAI_API_KEY:
        st.error("❌ OPENAI_API_KEY not found. Please set it in your .env file or environment variables.")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Navigation")
        page = st.radio(
            "Choose a section:",
            ["📚 Upload Textbooks", "❓ Ask Questions", "💡 Examples"]
        )
        
        st.markdown("---")
        st.markdown("## ℹ️ About")
        st.markdown("""
        This AI Educational Assistant uses RAG (Retrieval Augmented Generation) to provide accurate, 
        textbook-based answers to educational questions.
        
        **Features:**
        - 📚 PDF and text file processing
        - 🧠 Smart text chunking
        - 🔍 Semantic search
        - 💡 Context-aware answers
        - 📖 Grade-appropriate responses
        """)
    
    # Main content
    if page == "📚 Upload Textbooks":
        upload_textbooks()
    
    elif page == "❓ Ask Questions":
        # Check if example question was selected
        question = None
        if hasattr(st.session_state, 'example_question'):
            question = st.session_state.example_question
            del st.session_state.example_question
        
        ask_questions(question)
    
    elif page == "💡 Examples":
        example_questions()

if __name__ == "__main__":
    main()
