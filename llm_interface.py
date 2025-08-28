from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import Document, HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
import logging

from config import Config
from prompt_templates import PromptTemplateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMInterface:
    """Handles LLM interactions for question answering."""
    
    def __init__(self, model_name: str = None, temperature: float = None, max_tokens: int = None):
        self.model_name = model_name or Config.OPENAI_MODEL
        self.temperature = temperature or Config.TEMPERATURE
        self.max_tokens = max_tokens or Config.MAX_TOKENS
        
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize prompt template manager
        self.prompt_manager = PromptTemplateManager()
        
        # Fallback prompt template for backward compatibility
        self.fallback_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an educational assistant designed to help students from grades 1-10. 
            Your role is to provide clear, accurate, and age-appropriate explanations based on the provided textbook content.
            
            Guidelines:
            1. Base your answers ONLY on the provided context from textbooks
            2. If the context doesn't contain enough information, say so clearly
            3. Use simple, clear language appropriate for the student's grade level
            4. Provide step-by-step explanations when helpful
            5. Include examples when possible
            6. Avoid technical jargon unless it's essential and explained
            7. Be encouraging and supportive in your tone
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a comprehensive, student-friendly answer based on the textbook content."""),
            ("human", "{question}")
        ])
    
    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string."""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source_info = f"Source: {doc.metadata.get('source', 'Unknown')}"
            grade_info = f"Grade: {doc.metadata.get('grade', 'Not specified')}"
            subject_info = f"Subject: {doc.metadata.get('subject', 'Not specified')}"
            
            context_parts.append(f"--- Document {i} ---")
            context_parts.append(f"{source_info} | {grade_info} | {subject_info}")
            context_parts.append(doc.page_content)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def answer_question(self, question: str, context_documents: List[Document]) -> Dict[str, Any]:
        """Generate an answer to a question using the provided context."""
        try:
            # Format the context
            context = self.format_context(context_documents)
            
            # Get enhanced prompt using template manager
            enhanced_prompt = self.prompt_manager.get_enhanced_prompt(question, context)
            
            # Store template information for output
            template_info = {
                "question_type": enhanced_prompt['question_type'],
                "subject": enhanced_prompt['subject'],
                "grade_level": enhanced_prompt['grade_level'],
                "complexity": enhanced_prompt['complexity'],
                "keywords": enhanced_prompt['keywords'],
                "template_used": f"{enhanced_prompt['question_type']}_{enhanced_prompt['subject']}",
                "model": self.model_name,
                "context_documents_count": len(context_documents)
            }
            
            # Log the analysis for debugging
            logger.info(f"Question analysis: Type={enhanced_prompt['question_type']}, "
                       f"Subject={enhanced_prompt['subject']}, Grade={enhanced_prompt['grade_level']}")
            
            # Create the prompt using the enhanced template
            messages = [
                SystemMessage(content=enhanced_prompt["prompt"]),
                HumanMessage(content=question)
            ]
            
            # Generate response
            logger.info(f"Calling LLM with model: {self.model_name}")
            response = self.llm.invoke(messages)
            logger.info(f"Received response: {type(response)} | Content length: {len(response.content) if hasattr(response, 'content') else 'No content'}")
            
            # Extract metadata from context documents
            sources = list(set([doc.metadata.get('source', 'Unknown') for doc in context_documents]))
            grades = list(set([doc.metadata.get('grade', 'Not specified') for doc in context_documents]))
            subjects = list(set([doc.metadata.get('subject', 'Not specified') for doc in context_documents]))
            
            result = {
                "answer": response.content,
                "sources": sources,
                "grades": grades,
                "subjects": subjects,
                "context_documents_count": len(context_documents),
                "model_used": self.model_name,
                "template_info": template_info,
                "question_analysis": {
                    "type": enhanced_prompt["question_type"],
                    "subject": enhanced_prompt["subject"],
                    "grade_level": enhanced_prompt["grade_level"],
                    "complexity": enhanced_prompt["complexity"]
                }
            }
            
            logger.info(f"Generated answer for question: {question[:50]}... | Answer preview: {result['answer'][:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def answer_question_with_chain(self, question: str, context_documents: List[Document]) -> Dict[str, Any]:
        """Alternative method using LangChain's chain approach."""
        try:
            # Format the context
            context = self.format_context(context_documents)
            
            # Create a simple chain
            chain = self.prompt_template | self.llm
            
            # Run the chain
            response = chain.invoke({
                "context": context,
                "question": question
            })
            
            # Extract metadata
            sources = list(set([doc.metadata.get('source', 'Unknown') for doc in context_documents]))
            grades = list(set([doc.metadata.get('grade', 'Not specified') for doc in context_documents]))
            subjects = list(set([doc.metadata.get('subject', 'Not specified') for doc in context_documents]))
            
            result = {
                "answer": response.content,
                "sources": sources,
                "grades": grades,
                "subjects": subjects,
                "context_documents_count": len(context_documents),
                "model_used": self.model_name
            }
            
            logger.info(f"Generated answer using chain for question: {question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer with chain: {str(e)}")
            raise
