"""
Prompt Templates for Educational Assistant

This module provides a comprehensive system for categorizing educational questions
and applying appropriate prompt templates to guide the LLM responses.
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class QuestionType(Enum):
    """Enumeration of different question types."""
    EXPLANATION = "explanation"
    DEFINITION = "definition"
    STEP_BY_STEP = "step_by_step"
    COMPARISON = "comparison"
    PROBLEM_SOLVING = "problem_solving"
    CONCEPT_APPLICATION = "concept_application"
    EXAMPLES = "examples"
    SUMMARY = "summary"
    QUIZ = "quiz"
    GENERAL = "general"

class Subject(Enum):
    """Enumeration of different subjects."""
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HINDI = "hindi"
    SOCIAL_STUDIES = "social_studies"
    ENVIRONMENTAL_STUDIES = "environmental_studies"
    ARTS = "arts"
    PHYSICAL_EDUCATION = "physical_education"
    GENERAL = "general"

@dataclass
class QuestionAnalysis:
    """Data class to hold question analysis results."""
    question_type: QuestionType
    subject: Subject
    grade_level: Optional[str]
    keywords: List[str]
    complexity: str  # "basic", "intermediate", "advanced"

class PromptTemplateManager:
    """Manages prompt templates for different types of educational questions."""
    
    def __init__(self):
        self.question_patterns = self._initialize_question_patterns()
        self.templates = self._initialize_templates()
    
    def _initialize_question_patterns(self) -> Dict[QuestionType, List[str]]:
        """Initialize patterns for question type detection."""
        return {
            QuestionType.EXPLANATION: [
                r'\b(explain|describe|tell me about|what is|how does|why does)\b',
                r'\b(explanation|description|overview)\b',
                r'\b(teach me about|help me understand)\b'
            ],
            QuestionType.DEFINITION: [
                r'\b(define|what is the definition of|meaning of)\b',
                r'\b(what do you mean by|what does.*mean)\b',
                r'\b(define.*as|definition)\b'
            ],
            QuestionType.STEP_BY_STEP: [
                r'\b(step by step|steps|process|procedure)\b',
                r'\b(how to|how do you|method)\b',
                r'\b(sequence|order|first.*then)\b'
            ],
            QuestionType.COMPARISON: [
                r'\b(compare|difference between|similarities|contrast)\b',
                r'\b(vs|versus|unlike|like)\b',
                r'\b(same as|different from|similar to)\b'
            ],
            QuestionType.PROBLEM_SOLVING: [
                r'\b(solve|calculate|find|compute|work out)\b',
                r'\b(problem|equation|formula|math)\b',
                r'\b(how many|how much|what is the answer)\b'
            ],
            QuestionType.CONCEPT_APPLICATION: [
                r'\b(apply|use|implement|practice)\b',
                r'\b(real life|everyday|example of)\b',
                r'\b(how would you|what would happen if)\b'
            ],
            QuestionType.EXAMPLES: [
                r'\b(example|instance|case|sample)\b',
                r'\b(give me.*example|show me.*example)\b',
                r'\b(such as|like|for instance)\b'
            ],
            QuestionType.SUMMARY: [
                r'\b(summarize|summary|brief|overview)\b',
                r'\b(main points|key points|important)\b',
                r'\b(in short|in brief|conclude)\b'
            ],
            QuestionType.QUIZ: [
                r'\b(quiz|test|question|multiple choice)\b',
                r'\b(true or false|fill in the blank)\b',
                r'\b(practice question|exercise)\b'
            ]
        }
    
    def _initialize_templates(self) -> Dict[Tuple[QuestionType, Subject], str]:
        """Initialize prompt templates for different question types and subjects."""
        templates = {}
        
        # Base templates for each question type
        base_templates = {
            QuestionType.EXPLANATION: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a clear, engaging explanation that:
            1. Uses simple, age-appropriate language
            2. Breaks down complex concepts into digestible parts
            3. Uses analogies or examples that students can relate to
            4. Encourages curiosity and further learning
            5. Relates the concept to real-world applications when possible
            
            Make your explanation conversational and encouraging, as if you're talking directly to the student.""",
            
            QuestionType.DEFINITION: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a clear definition that:
            1. Uses simple, precise language appropriate for the grade level
            2. Explains the concept in multiple ways if helpful
            3. Provides a simple example to illustrate the definition
            4. Connects the definition to what the student already knows
            5. Avoids unnecessary technical jargon
            
            Make the definition memorable and easy to understand.""",
            
            QuestionType.STEP_BY_STEP: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a step-by-step explanation that:
            1. Breaks down the process into clear, numbered steps
            2. Explains why each step is important
            3. Uses simple language appropriate for the grade level
            4. Includes helpful tips or warnings where relevant
            5. Provides a simple example if possible
            6. Encourages the student to practice the steps
            
            Make each step clear and actionable.""",
            
            QuestionType.COMPARISON: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a comparison that:
            1. Clearly identifies the similarities and differences
            2. Uses a structured format (e.g., table or bullet points)
            3. Uses simple, clear language appropriate for the grade level
            4. Provides concrete examples for each point
            5. Helps the student understand when to use each concept
            6. Uses visual language to help the student picture the differences
            
            Make the comparison easy to understand and remember.""",
            
            QuestionType.PROBLEM_SOLVING: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a problem-solving approach that:
            1. Shows the step-by-step solution process
            2. Explains the reasoning behind each step
            3. Uses simple language appropriate for the grade level
            4. Provides helpful tips and strategies
            5. Encourages the student to think through the problem
            6. Shows how to check if the answer makes sense
            
            Make the solution process clear and educational.""",
            
            QuestionType.CONCEPT_APPLICATION: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please explain how to apply this concept by:
            1. Showing real-world examples and applications
            2. Explaining when and why this concept is useful
            3. Using simple, relatable examples
            4. Encouraging the student to think of their own examples
            5. Connecting to the student's everyday experiences
            6. Making the application practical and meaningful
            
            Help the student see the value and usefulness of this concept.""",
            
            QuestionType.EXAMPLES: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide examples that:
            1. Are relevant and interesting to students of this age
            2. Use simple, clear language
            3. Show different types or variations of the concept
            4. Help the student understand the concept better
            5. Are easy to remember and relate to
            6. Encourage the student to think of their own examples
            
            Make the examples engaging and educational.""",
            
            QuestionType.SUMMARY: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a summary that:
            1. Captures the most important points clearly
            2. Uses simple, organized language
            3. Highlights key concepts and ideas
            4. Helps the student remember the main points
            5. Connects different parts of the topic
            6. Provides a clear overview for understanding
            
            Make the summary concise but comprehensive.""",
            
            QuestionType.QUIZ: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please create a quiz or practice question that:
            1. Tests understanding of the key concepts
            2. Uses clear, simple language appropriate for the grade level
            3. Provides helpful feedback and explanations
            4. Encourages critical thinking
            5. Makes learning fun and engaging
            6. Helps the student practice and reinforce learning
            
            Make the quiz educational and encouraging.""",
            
            QuestionType.GENERAL: """You are an educational assistant helping a {grade_level} student understand {subject}.
            
            Context from textbooks:
            {context}
            
            Student's question: {question}
            
            Please provide a helpful answer that:
            1. Uses clear, age-appropriate language
            2. Is based on the provided textbook content
            3. Encourages learning and curiosity
            4. Provides useful information and insights
            5. Helps the student understand the topic better
            6. Is supportive and encouraging in tone
            
            Make your response educational and engaging."""
        }
        
        # Subject-specific modifications
        subject_modifications = {
            Subject.MATHEMATICS: {
                "additional_guidelines": """
                - Use clear mathematical notation when helpful
                - Show step-by-step calculations
                - Emphasize problem-solving strategies
                - Connect math to real-world applications
                - Use visual language to describe mathematical concepts
                """,
                "examples": "Use everyday examples like counting objects, measuring things, or sharing items."
            },
            Subject.SCIENCE: {
                "additional_guidelines": """
                - Explain scientific concepts using simple analogies
                - Connect to everyday observations
                - Emphasize the scientific method and curiosity
                - Use simple experiments or demonstrations when possible
                - Explain cause and effect relationships clearly
                """,
                "examples": "Use examples from nature, weather, cooking, or everyday activities."
            },
            Subject.ENGLISH: {
                "additional_guidelines": """
                - Use clear, correct grammar and vocabulary
                - Provide examples of good writing
                - Explain language concepts with simple examples
                - Encourage reading and writing skills
                - Use age-appropriate literature examples
                """,
                "examples": "Use examples from stories, poems, or everyday conversations."
            },
            Subject.HINDI: {
                "additional_guidelines": """
                - Use clear, correct Hindi grammar and vocabulary
                - Provide examples of good Hindi writing
                - Explain language concepts with simple examples
                - Encourage reading and writing skills in Hindi
                - Use age-appropriate Hindi literature examples
                """,
                "examples": "Use examples from Hindi stories, poems, or everyday conversations."
            },
            Subject.SOCIAL_STUDIES: {
                "additional_guidelines": """
                - Connect historical events to the present
                - Explain cultural and social concepts clearly
                - Use maps and geographical references when helpful
                - Emphasize the importance of different perspectives
                - Connect to students' own communities and experiences
                """,
                "examples": "Use examples from local history, current events, or family traditions."
            },
            Subject.ENVIRONMENTAL_STUDIES: {
                "additional_guidelines": """
                - Connect environmental concepts to students' surroundings
                - Emphasize the importance of caring for the environment
                - Use local examples and observations
                - Encourage environmental awareness and responsibility
                - Connect to students' daily activities and choices
                """,
                "examples": "Use examples from the school environment, home, or local community."
            }
        }
        
        # Create templates for each combination
        for question_type in QuestionType:
            for subject in Subject:
                base_template = base_templates[question_type]
                
                # Add subject-specific modifications
                if subject in subject_modifications:
                    mod = subject_modifications[subject]
                    base_template += f"\n\nAdditional guidelines for {subject.value}:\n{mod['additional_guidelines']}"
                    base_template += f"\n\nExamples: {mod['examples']}"
                
                templates[(question_type, subject)] = base_template
        
        return templates
    
    def analyze_question(self, question: str) -> QuestionAnalysis:
        """Analyze a question to determine its type, subject, and other characteristics."""
        question_lower = question.lower()
        
        # Determine question type
        question_type = QuestionType.GENERAL
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    question_type = q_type
                    break
            if question_type != QuestionType.GENERAL:
                break
        
        # Determine subject
        subject = Subject.GENERAL
        subject_keywords = {
            Subject.MATHEMATICS: ['math', 'mathematics', 'number', 'calculate', 'equation', 'geometry', 'algebra', 'fraction', 'decimal', 'percentage'],
            Subject.SCIENCE: ['science', 'physics', 'chemistry', 'biology', 'experiment', 'scientific', 'matter', 'energy', 'plant', 'animal', 'cell'],
            Subject.ENGLISH: ['english', 'grammar', 'vocabulary', 'sentence', 'paragraph', 'story', 'poem', 'reading', 'writing'],
            Subject.HINDI: ['hindi', 'हिंदी', 'व्याकरण', 'कहानी', 'कविता', 'पढ़ना', 'लिखना'],
            Subject.SOCIAL_STUDIES: ['history', 'geography', 'social', 'culture', 'country', 'government', 'citizen', 'community'],
            Subject.ENVIRONMENTAL_STUDIES: ['environment', 'environmental', 'nature', 'pollution', 'conservation', 'ecosystem', 'climate']
        }
        
        for subj, keywords in subject_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                subject = subj
                break
        
        # Determine grade level
        grade_level = "elementary"
        grade_patterns = {
            r'\b(class\s*[1-5]|grade\s*[1-5])\b': "primary",
            r'\b(class\s*[6-8]|grade\s*[6-8])\b': "middle",
            r'\b(class\s*[9]|grade\s*[9]|class\s*10|grade\s*10)\b': "secondary"
        }
        
        for pattern, grade in grade_patterns.items():
            if re.search(pattern, question_lower):
                grade_level = grade
                break
        
        # Extract keywords
        keywords = [word for word in question_lower.split() if len(word) > 3]
        
        # Determine complexity
        complexity = "basic"
        if any(word in question_lower for word in ['complex', 'advanced', 'difficult', 'challenging']):
            complexity = "advanced"
        elif any(word in question_lower for word in ['intermediate', 'moderate', 'medium']):
            complexity = "intermediate"
        
        return QuestionAnalysis(
            question_type=question_type,
            subject=subject,
            grade_level=grade_level,
            keywords=keywords,
            complexity=complexity
        )
    
    def get_template(self, question_analysis: QuestionAnalysis) -> str:
        """Get the appropriate template for the analyzed question."""
        template_key = (question_analysis.question_type, question_analysis.subject)
        return self.templates.get(template_key, self.templates.get((QuestionType.GENERAL, Subject.GENERAL)))
    
    def format_prompt(self, question: str, context: str, question_analysis: QuestionAnalysis) -> str:
        """Format the prompt using the appropriate template."""
        template = self.get_template(question_analysis)
        
        return template.format(
            question=question,
            context=context,
            grade_level=question_analysis.grade_level,
            subject=question_analysis.subject.value
        )
    
    def get_enhanced_prompt(self, question: str, context: str) -> Dict[str, any]:
        """Get an enhanced prompt with analysis and formatted template."""
        analysis = self.analyze_question(question)
        formatted_prompt = self.format_prompt(question, context, analysis)
        
        return {
            "prompt": formatted_prompt,
            "analysis": analysis,
            "question_type": analysis.question_type.value,
            "subject": analysis.subject.value,
            "grade_level": analysis.grade_level,
            "complexity": analysis.complexity,
            "keywords": analysis.keywords
        }

# Example usage and sample templates
SAMPLE_TEMPLATES = {
    "math_problem_solving": """You are an educational assistant helping a {grade_level} student understand mathematics.

Context from textbooks:
{context}

Student's question: {question}

Please provide a problem-solving approach that:
1. Shows the step-by-step solution process
2. Explains the reasoning behind each step
3. Uses simple language appropriate for the grade level
4. Provides helpful tips and strategies
5. Encourages the student to think through the problem
6. Shows how to check if the answer makes sense

Additional guidelines for mathematics:
- Use clear mathematical notation when helpful
- Show step-by-step calculations
- Emphasize problem-solving strategies
- Connect math to real-world applications
- Use visual language to describe mathematical concepts

Examples: Use everyday examples like counting objects, measuring things, or sharing items.

Make the solution process clear and educational.""",

    "science_explanation": """You are an educational assistant helping a {grade_level} student understand science.

Context from textbooks:
{context}

Student's question: {question}

Please provide a clear, engaging explanation that:
1. Uses simple, age-appropriate language
2. Breaks down complex concepts into digestible parts
3. Uses analogies or examples that students can relate to
4. Encourages curiosity and further learning
5. Relates the concept to real-world applications when possible

Additional guidelines for science:
- Explain scientific concepts using simple analogies
- Connect to everyday observations
- Emphasize the scientific method and curiosity
- Use simple experiments or demonstrations when possible
- Explain cause and effect relationships clearly

Examples: Use examples from nature, weather, cooking, or everyday activities.

Make your explanation conversational and encouraging, as if you're talking directly to the student.""",

    "english_grammar": """You are an educational assistant helping a {grade_level} student understand english.

Context from textbooks:
{context}

Student's question: {question}

Please provide a clear definition that:
1. Uses simple, precise language appropriate for the grade level
2. Explains the concept in multiple ways if helpful
3. Provides a simple example to illustrate the definition
4. Connects the definition to what the student already knows
5. Avoids unnecessary technical jargon

Additional guidelines for english:
- Use clear, correct grammar and vocabulary
- Provide examples of good writing
- Explain language concepts with simple examples
- Encourage reading and writing skills
- Use age-appropriate literature examples

Examples: Use examples from stories, poems, or everyday conversations.

Make the definition memorable and easy to understand.""",

    "social_studies_comparison": """You are an educational assistant helping a {grade_level} student understand social_studies.

Context from textbooks:
{context}

Student's question: {question}

Please provide a comparison that:
1. Clearly identifies the similarities and differences
2. Uses a structured format (e.g., table or bullet points)
3. Uses simple, clear language appropriate for the grade level
4. Provides concrete examples for each point
5. Helps the student understand when to use each concept
6. Uses visual language to help the student picture the differences

Additional guidelines for social_studies:
- Connect historical events to the present
- Explain cultural and social concepts clearly
- Use maps and geographical references when helpful
- Emphasize the importance of different perspectives
- Connect to students' own communities and experiences

Examples: Use examples from local history, current events, or family traditions.

Make the comparison easy to understand and remember."""
}

if __name__ == "__main__":
    # Example usage
    manager = PromptTemplateManager()
    
    # Test questions
    test_questions = [
        "Explain photosynthesis for Class 6",
        "What is the difference between a plant cell and an animal cell?",
        "How do I solve this math problem: 2x + 5 = 13?",
        "Give me examples of proper nouns",
        "Summarize the water cycle for Class 5",
        "What is the definition of gravity?"
    ]
    
    for question in test_questions:
        analysis = manager.analyze_question(question)
        print(f"\nQuestion: {question}")
        print(f"Type: {analysis.question_type.value}")
        print(f"Subject: {analysis.subject.value}")
        print(f"Grade: {analysis.grade_level}")
        print(f"Complexity: {analysis.complexity}")
        print(f"Keywords: {analysis.keywords}")
