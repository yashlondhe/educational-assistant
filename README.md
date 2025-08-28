# AI Educational Assistant

A comprehensive AI-powered educational assistant that uses RAG (Retrieval Augmented Generation) to provide accurate, textbook-based answers to educational questions for students in grades 1-10.

## 🎯 Features

- **📚 Textbook Processing**: Extract text from PDF and text files
- **🧠 Smart Chunking**: Intelligent text segmentation for optimal retrieval
- **🔍 Semantic Search**: Find relevant content using vector embeddings
- **💡 Context-Aware Answers**: Generate answers based only on textbook content
- **📖 Grade-Appropriate Responses**: Tailored explanations for different grade levels
- **🎯 Smart Prompt Templates**: Automatic question analysis and specialized templates
- **🌐 Multiple Interfaces**: CLI and Streamlit web interface
- **🗄️ Vector Database Support**: Chroma and FAISS vector stores
- **🤖 LLM Integration**: OpenAI GPT-4o-mini for answer generation (optimized for educational content)

## 🏗️ Architecture

The system follows a modular RAG architecture with intelligent prompt templating:

1. **Text Processing**: Extract and chunk text from textbooks
2. **Embedding Generation**: Convert text chunks into vector embeddings
3. **Vector Storage**: Store embeddings in a vector database
4. **Retrieval**: Find relevant context for user questions
5. **Question Analysis**: Automatically categorize questions by type, subject, and grade level
6. **Template Selection**: Choose appropriate prompt template based on analysis
7. **Answer Generation**: Use LLM with specialized prompts to generate context-aware answers

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

## 📖 Usage

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

### Streamlit Web Interface

```bash
# Start the web interface
streamlit run streamlit_app.py
```

The web interface provides:
- 📚 Textbook upload and processing
- ❓ Interactive question-answering
- 💡 Example questions
- 📊 Database information
- ⚙️ Advanced configuration options

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
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .env                    # Environment variables
├── textbooks/              # Textbook files directory
├── example_textbooks/      # Sample textbooks
├── chroma_db/             # Chroma database storage
└── output/                # Output directory
```

## 🧪 Example Usage

### 1. Setup with Sample Textbooks

```bash
# Copy sample textbooks to textbooks directory
cp example_textbooks/* textbooks/

# Setup database
python cli.py setup --textbooks-dir ./textbooks
```

### 2. Ask Questions

```bash
# Interactive mode
python cli.py interactive

# Single question
python cli.py ask "What are the different types of triangles?"
```

### 3. Web Interface

```bash
streamlit run streamlit_app.py
```

Then visit `http://localhost:8501` in your browser.

## 📝 Example Questions and Answers

**Question**: "Explain photosynthesis for Class 6"

**Answer**: Photosynthesis is the process by which plants make their own food using sunlight, water, and carbon dioxide. This amazing process happens in the green parts of plants, especially in the leaves.

The process involves:
1. Plants take in carbon dioxide from the air through tiny holes called stomata
2. Water is absorbed by the roots and transported to the leaves
3. Sunlight is captured by a green pigment called chlorophyll
4. These ingredients combine to produce glucose (sugar) and oxygen
5. The glucose is used as food for the plant, and oxygen is released into the air

**Question**: "What are the different types of triangles?"

**Answer**: There are several ways to classify triangles:

**By Sides:**
1. Equilateral Triangle: All three sides are equal in length
2. Isosceles Triangle: Two sides are equal in length
3. Scalene Triangle: All three sides have different lengths

**By Angles:**
1. Acute Triangle: All three angles are less than 90 degrees
2. Right Triangle: One angle is exactly 90 degrees
3. Obtuse Triangle: One angle is greater than 90 degrees

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

### Benefits
- **Better Responses**: More accurate and appropriate answers
- **Age-Appropriate Language**: Tailored to student grade level
- **Subject-Specific Guidance**: Specialized instructions for different subjects
- **Consistent Quality**: Standardized approach to different question types

## 🔍 How It Works

1. **Text Processing**: PDFs and text files are processed to extract text content
2. **Chunking**: Text is split into manageable chunks (default: 1000 tokens with 200 token overlap)
3. **Embedding**: Each chunk is converted to a vector embedding using OpenAI's embedding model
4. **Storage**: Embeddings are stored in a vector database (Chroma or FAISS)
5. **Retrieval**: When a question is asked, the system finds the most relevant chunks
6. **Question Analysis**: The system analyzes the question type, subject, and grade level
7. **Template Selection**: Appropriate prompt template is selected based on analysis
8. **Answer Generation**: The LLM generates an answer using specialized prompts and retrieved context

## 🛠️ Development

### Adding New Features

1. **New Vector Database**: Extend `vector_store.py` to support additional databases
2. **New LLM Provider**: Modify `llm_interface.py` to support other LLM providers
3. **New File Format**: Add support in `text_processor.py` for additional file types

### Testing

```bash
# Test the CLI
python cli.py setup --textbooks-dir ./example_textbooks
python cli.py ask "What is photosynthesis?"

# Test the web interface
streamlit run streamlit_app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

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
2. Ensure all dependencies are installed
3. Verify that textbook files are in the correct format
4. Check the logs for detailed error messages

For additional help, please open an issue on the repository.
