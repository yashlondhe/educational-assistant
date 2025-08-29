# AI Educational Assistant

A comprehensive AI-powered educational assistant that uses RAG (Retrieval Augmented Generation) to provide accurate, textbook-based answers to educational questions for students in grades 1-10.

## 🎯 Features

### Core Features
- **📚 Textbook Processing**: Extract text from PDF and text files
- **🧠 Smart Chunking**: Intelligent text segmentation for optimal retrieval
- **🔍 Semantic Search**: Find relevant content using vector embeddings
- **💡 Context-Aware Answers**: Generate answers based only on textbook content
- **📖 Grade-Appropriate Responses**: Tailored explanations for different grade levels
- **🎯 Smart Prompt Templates**: Automatic question analysis and specialized templates
- **🌐 Multiple Interfaces**: CLI and Streamlit web interface
- **🗄️ Vector Database Support**: Chroma and FAISS vector stores
- **🤖 LLM Integration**: OpenAI GPT-4o-mini for answer generation (optimized for educational content)

### User Management Features
- **🔐 User Authentication**: Secure registration and login system
- **👤 User Profile Management**: Personal profiles with class and subject preferences
- **📚 Personalized Content Selection**: Class-based subject and textbook filtering
- **❓ Filtered Question Answering**: Answers based only on user's selected textbooks
- **📊 Learning Analytics**: Progress tracking and learning insights

### Advanced Features
- **🗂️ Conversation History**: Progressive compression system for chat history
- **🧠 Context-Aware Conversations**: Intelligent context detection for follow-up questions
- **📈 Learning Profiles**: Automated generation of user learning patterns
- **⚡ Efficient Storage**: Hybrid compression reducing storage by 80-95%
- **🔄 Automated Maintenance**: Scheduled compression and cleanup

## 🏗️ Architecture

The system follows a modular RAG architecture with intelligent features:

1. **Text Processing**: Extract and chunk text from textbooks
2. **Embedding Generation**: Convert text chunks into vector embeddings
3. **Vector Storage**: Store embeddings in a vector database
4. **User Management**: Handle authentication, profiles, and content selection
5. **Retrieval**: Find relevant context for user questions with personalized filtering
6. **Question Analysis**: Automatically categorize questions by type, subject, and grade level
7. **Template Selection**: Choose appropriate prompt template based on analysis
8. **Answer Generation**: Use LLM with specialized prompts to generate context-aware answers
9. **History Management**: Progressive compression and context detection for conversations

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Internet connection (for API calls)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd educational-assistant
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=text-embedding-ada-002
   VECTOR_DB_TYPE=chroma
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   ```

4. **Initialize the database**:
   ```bash
   python initialize_database.py
   ```

## 📖 Usage

### Streamlit Web Interface (Recommended)

```bash
# Start the web interface
streamlit run streamlit_app.py
```

The web interface provides:
- 🔐 User authentication (login/register)
- 👤 User profile management with class selection
- 📚 Personalized content selection (subjects and textbooks)
- ❓ Interactive question-answering with filtered results
- 📊 Learning analytics and conversation history
- ⚙️ Advanced configuration options

### Command Line Interface

#### 1. Setup Database with Textbooks

```bash
# Set up database with textbooks from a directory
python cli.py setup --textbooks-dir ./textbooks

# Use FAISS instead of Chroma
python cli.py setup --textbooks-dir ./textbooks --db-type faiss
```

#### 2. Interactive Mode

```bash
# Start interactive question-answering session
python cli.py interactive

# Use FAISS database
python cli.py interactive --db-type faiss
```

#### 3. Ask Single Questions

```bash
# Ask a specific question
python cli.py ask "Explain photosynthesis for Class 6"

# Get database information
python cli.py info
```

## 👤 User Authentication & Profiles

### User Registration
New users provide:
- Email address (unique identifier)
- Password (minimum 6 characters)
- Full name
- Class (1-10)
- Date of birth (optional)
- Phone number (optional)

### Content Selection Hierarchy
1. **Class-based Navigation**: Content filtered by user's class
2. **Subject Selection**: Choose one subject at a time
3. **Textbook Selection**: Select multiple textbooks within subject
4. **Mandatory Selection**: At least one subject and textbook required

### Personalized Experience
- **Filtered Search**: Only searches within selected textbooks
- **Class-aware Responses**: Answers tailored to user's grade level
- **Selection Validation**: Ensures valid selections before answering
- **Learning Tracking**: Monitors progress and preferences

## 🗂️ Conversation History & Compression

### Progressive Compression System

The system implements a 4-level compression strategy:

#### 1. **NONE (< 7 days)**
- **Storage**: Full conversation data
- **Contains**: Complete questions and answers
- **Location**: `user_history/<user_id>/session_*.json`

#### 2. **LIGHT (7-30 days)**
- **Storage**: Questions + Answer summaries
- **Compression**: Long answers (>500 chars) summarized to 2-3 sentences
- **Location**: `user_history_compressed/<user_id>/<session_id>_light.json`

#### 3. **MEDIUM (30-90 days)**
- **Storage**: Summary + Important Q&A pairs + Learning outcomes
- **Compression**: Only top 3 most important Q&A pairs kept
- **Location**: `user_history_compressed/<user_id>/<session_id>_medium.json`

#### 4. **HEAVY (> 90 days)**
- **Storage**: Learning insights only
- **Compression**: Session metadata and insights, no Q&A content
- **Location**: `user_history_compressed/<user_id>/<session_id>_heavy.json`

### Automated Compression

Set up automatic compression:

```bash
# Set up daily compression (runs at 2 AM)
python compression_scheduler.py --setup-cron

# Manual compression
python compression_scheduler.py

# Test compression system
python compression_scheduler.py --dry-run
```

### Learning Profiles

The system automatically generates learning profiles:

```json
{
  "total_sessions": 45,
  "total_questions": 523,
  "unique_concepts": 128,
  "preferred_topics": ["mathematics", "science", "history"],
  "learning_style": "deep_explorer",
  "topic_mastery": {
    "photosynthesis": 0.85,
    "algebra": 0.65,
    "grammar": 0.75
  }
}
```

## 📚 Textbook Format

The system automatically extracts grade and subject information from filenames:

**Naming Convention**: `[subject]_[grade].pdf` or `[subject]_[grade].txt`

**Examples**:
- `science_grade6.pdf` → Grade 6, Science
- `math_class5.txt` → Grade 5, Mathematics
- `biology_std7.pdf` → Grade 7, Biology

**Supported Subjects**: math, science, english, history, geography, civics, physics, chemistry, biology

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model for answer generation |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Model for generating embeddings |
| `VECTOR_DB_TYPE` | `chroma` | Vector database type (`chroma` or `faiss`) |
| `CHUNK_SIZE` | `1000` | Size of text chunks |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Number of context documents to retrieve |
| `MAX_TOKENS` | `1000` | Maximum tokens for LLM response |
| `TEMPERATURE` | `0.7` | LLM temperature setting |

### File Structure

```
educational-assistant/
├── config.py                 # Configuration management
├── text_processor.py         # Text extraction and chunking
├── vector_store.py          # Vector database operations
├── llm_interface.py         # LLM integration
├── educational_assistant.py # Main assistant class
├── cli.py                   # Command line interface
├── streamlit_app.py         # Web interface
├── database.py              # SQLite database management
├── auth.py                  # User authentication
├── user_manager.py          # User and content management
├── content_manager.py       # NCERT content structure
├── history_manager.py       # Conversation history & compression
├── compression_scheduler.py # Automated compression
├── initialize_database.py   # Database initialization
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .env                    # Environment variables
├── textbooks/              # Textbook files directory
├── NCERT_Textbooks/        # NCERT textbook collection
├── user_history/           # Recent conversation history
├── user_history_compressed/ # Compressed historical data
├── chroma_db/             # Chroma database storage
└── output/                # Output directory
```

## 🎯 Smart Prompt Template System

The educational assistant uses an intelligent prompt template system that automatically analyzes questions and applies specialized templates for better responses.

### Question Analysis
The system automatically categorizes each question by:
- **Question Type**: explanation, definition, problem-solving, comparison, step-by-step, concept application, examples, summary, quiz
- **Subject**: mathematics, science, english, hindi, social studies, environmental studies
- **Grade Level**: primary (1-5), middle (6-8), secondary (9-10)
- **Complexity**: basic, intermediate, advanced

### Template Examples

**Mathematics Problem-Solving**:
- Step-by-step solution process
- Clear mathematical notation
- Problem-solving strategies
- Real-world applications

**Science Explanation**:
- Simple analogies and examples
- Everyday observations
- Scientific curiosity encouragement
- Cause-and-effect relationships

**English Grammar**:
- Clear, correct grammar examples
- Age-appropriate literature references
- Writing and reading encouragement
- Simple, memorable explanations

## 🧪 Testing

### System Testing
```bash
# Test the complete system
python test_system.py

# Test compression system
python test_compression_system.py

# Test CLI functionality
python cli.py setup --textbooks-dir ./example_textbooks
python cli.py ask "What is photosynthesis?"
```

### Web Interface Testing
```bash
# Start the web interface
streamlit run streamlit_app.py
```

Then visit `http://localhost:8501` in your browser.

## 📝 Example Usage

### 1. Web Interface Flow

1. **Registration/Login**
   - New users register with their details
   - Existing users login with email/password

2. **Content Selection**
   - System shows subjects for user's class
   - User selects one subject
   - User selects one or more textbooks

3. **Ask Questions**
   - Questions are answered using only selected textbooks
   - Responses are tailored to user's class level
   - Context from previous conversations is automatically detected

4. **Profile Management**
   - Users can update their profile
   - Class changes affect available content

### 2. Example Questions and Answers

**Question**: "Explain photosynthesis for Class 6"

**Answer**: Photosynthesis is the process by which plants make their own food using sunlight, water, and carbon dioxide. This amazing process happens in the green parts of plants, especially in the leaves.

The process involves:
1. Plants take in carbon dioxide from the air through tiny holes called stomata
2. Water is absorbed by the roots and transported to the leaves
3. Sunlight is captured by a green pigment called chlorophyll
4. These ingredients combine to produce glucose (sugar) and oxygen
5. The glucose is used as food for the plant, and oxygen is released into the air

## 🔒 Security Features

- **Password Security**: SHA-256 hashing with salt (not stored in plain text)
- **Session Management**: Secure authentication sessions
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Parameterized queries throughout
- **Data Privacy**: Automatic compression and cleanup of old conversations

## 📊 Database Structure

```
users
├── email (unique)
├── password_hash
└── timestamps

user_profiles
├── user_id (FK)
├── name
├── class_grade
├── date_of_birth
└── phone_number

classes → subjects → textbooks
        (1:many)    (1:many)

user_selections
├── user_id
├── subject_id
└── textbook_ids

user_conversation_history
├── session_id
├── compression_level
├── learning_insights
└── conversation_data

user_learning_profiles
├── user_id
├── total_sessions
├── learning_style
└── topic_mastery
```

## 🚀 Performance & Benefits

### Storage Efficiency
- **80-95% reduction** in storage for old sessions
- **Automatic cleanup** of detailed data
- **Fast retrieval** of recent sessions

### Learning Insights
- **Preserves educational value** through intelligent compression
- **Tracks learning progress** over time
- **Identifies learning patterns** and preferences
- **Generates personalized recommendations**

### User Experience
- **Seamless context-aware** conversations
- **Personalized content** based on selections
- **Progressive learning** tracking
- **Intelligent question** handling

## 🛠️ Development

### Adding New Features

1. **New Vector Database**: Extend `vector_store.py` to support additional databases
2. **New LLM Provider**: Modify `llm_interface.py` to support other LLM providers
3. **New File Format**: Add support in `text_processor.py` for additional file types
4. **Custom Compression**: Extend `history_manager.py` for specialized compression rules

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🔮 Future Enhancements

### Planned Features
1. **OAuth Integration**: Google/GitHub login
2. **Multi-subject Selection**: Select multiple subjects simultaneously
3. **Advanced Analytics**: Dashboard showing learning statistics
4. **Quiz Generation**: Automated quizzes based on selections
5. **Collaborative Features**: Study groups and shared content

### Technical Improvements
1. **S3 Integration**: Store compressed files in AWS S3
2. **ML-Based Compression**: Use machine learning to identify important content
3. **Custom Compression Rules**: Per-user compression preferences
4. **API Development**: REST API for external integrations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT models and embedding APIs
- LangChain for the RAG framework
- Chroma and FAISS for vector database solutions
- Streamlit for the web interface framework

## 🆘 Support

If you encounter any issues:

1. Check that your OpenAI API key is correctly set
2. Ensure all dependencies are installed with `pip install -r requirements.txt`
3. Run `python initialize_database.py` to set up the database
4. Verify that textbook files are in the correct format
5. Check the logs for detailed error messages

For additional help, please open an issue on the repository.

## 📈 Status

**✅ PRODUCTION READY**

The AI Educational Assistant is fully implemented and tested, providing:
- Complete user authentication and profile management
- Intelligent conversation history with progressive compression
- Personalized content selection and filtering
- Context-aware question answering
- Automated learning analytics and insights

The system balances storage efficiency with educational value preservation, making it scalable for long-term educational use.