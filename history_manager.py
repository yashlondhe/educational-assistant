"""
Enhanced History Manager with progressive compression support.
Consolidated version containing all history management functionality.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import uuid

from database import Database
from llm_interface import LLMInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartContextDetector:
    """Hybrid context detector that combines rule-based and LLM-based detection."""
    
    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface
        
        # Quick patterns for definite history references
        self.history_patterns = [
            r"(?:what|can you|did|like|as)\s+(?:we\s+)?(?:discussed|talked|said|mentioned)",
            r"(?:from|in)\s+(?:our\s+)?(?:last|previous|earlier)\s+(?:conversation|session|discussion)",
            r"(?:remember|recall)\s+(?:when|what|that)",
            r"(?:continue|continuing)\s+(?:from|with|our)",
            r"(?:back\s+to|more\s+about)\s+(?:what|that|the)",
            r"follow\s*up",
            r"similarly|likewise",
            r"also|too\b",
            r"another\s+(?:example|question|problem)",
            r"more\s+(?:examples|questions|problems|details)",
            r"expand\s+on",
            r"tell\s+me\s+more",
            r"what\s+else",
            r"(?:any\s+)?other\s+(?:examples|ways|methods)",
            r"based\s+on\s+(?:what|our|that|this)"
        ]
        
        # Patterns that suggest no context needed
        self.no_context_patterns = [
            r"^(?:what|how|why|when|where|who)\s+(?:is|are|does|do|can)",
            r"^(?:define|explain|describe)\s+",
            r"^tell\s+me\s+about",
            r"^give\s+me\s+(?:an?\s+)?(?:example|definition)",
            r"^list\s+",
            r"^show\s+me"
        ]

    def should_fetch_history(self, question: str, user_id: int, db: Database) -> Tuple[bool, float, str]:
        """
        Determine if historical context should be fetched for this question.
        Returns (should_fetch, confidence, reason)
        """
        # Clean and prepare question
        clean_question = question.lower().strip()
        
        # Quick rule-based checks
        has_history_ref = any(re.search(pattern, clean_question) for pattern in self.history_patterns)
        has_no_context_pattern = any(re.search(pattern, clean_question) for pattern in self.no_context_patterns)
        
        # High confidence decisions
        if has_history_ref and not has_no_context_pattern:
            return True, 0.9, "Direct reference to previous conversation"
        
        if has_no_context_pattern and not has_history_ref:
            return False, 0.8, "Self-contained question pattern"
        
        # Check if question is contextually incomplete
        if self._is_contextually_incomplete(clean_question):
            return True, 0.7, "Question appears contextually incomplete"
        
        # Medium confidence - might need context
        if self._might_need_context(clean_question):
            # Use LLM for final decision
            llm_result = self._llm_classify(question)
            confidence = llm_result.get('confidence', 0.5)
            
            if llm_result.get('needs_context', False):
                return True, confidence, f"LLM classification: {llm_result.get('reason', 'Context likely helpful')}"
            else:
                return False, confidence, f"LLM classification: {llm_result.get('reason', 'Self-contained')}"
        
        return False, 0.6, "No clear indicators for context need"

    def _is_contextually_incomplete(self, question: str) -> bool:
        """Check if question seems to lack context."""
        incomplete_patterns = [
            r"^(?:more|another|different|other)(?:\s+\w+)?\s*\??$",
            r"^(?:that|this|it)\s+",
            r"^(?:how\s+about|what\s+about)\s+",
            r"^(?:can\s+you\s+)?(?:also|too)\s+",
            r"^(?:and|but|however)\s+",
            r"^(?:similarly|likewise)\s*,?",
            r"\b(?:same|similar)\s+(?:thing|way|method)\b",
            r"^(?:yes|no|ok|okay),?\s+"
        ]
        
        return any(re.search(pattern, question) for pattern in incomplete_patterns)

    def _might_need_context(self, question: str) -> bool:
        """Check if question might benefit from context."""
        context_helpful_patterns = [
            r"build\s+(?:on|upon)",
            r"improve\s+(?:on|upon)",
            r"better\s+(?:way|method|approach)",
            r"alternative\s+(?:way|method|approach)",
            r"different\s+(?:way|method|approach|perspective)",
            r"what\s+if",
            r"suppose",
            r"assuming",
            r"given\s+that"
        ]
        
        return any(re.search(pattern, question) for pattern in context_helpful_patterns)

    def _llm_classify(self, question: str) -> Dict[str, Any]:
        """Use LLM to classify if question needs historical context."""
        try:
            prompt = f"""Analyze this question and determine if it likely refers to or would benefit from previous conversation context.

Question: "{question}"

Respond with JSON containing:
- needs_context: boolean (true if likely needs context)
- confidence: number between 0 and 1
- reason: brief explanation
- type: "self_contained", "context_reference", or "context_helpful"

Examples:
- "What is photosynthesis?" -> {{"needs_context": false, "confidence": 0.9, "reason": "Complete standalone question", "type": "self_contained"}}
- "Can you give me more examples?" -> {{"needs_context": true, "confidence": 0.8, "reason": "Refers to previous examples", "type": "context_reference"}}
- "What about a different approach?" -> {{"needs_context": true, "confidence": 0.6, "reason": "Might build on previous discussion", "type": "context_helpful"}}
"""

            response = self.llm.generate_response(prompt, max_tokens=200)
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except:
                # Fallback if JSON parsing fails
                needs_context = any(word in response.lower() for word in ['true', 'yes', 'context', 'previous'])
                return {
                    "needs_context": needs_context,
                    "confidence": 0.5,
                    "reason": "LLM response parsing failed",
                    "type": "new_topic"
                }
                
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {
                "needs_context": False,
                "confidence": 0.3,
                "reason": "LLM classification error",
                "type": "new_topic"
            }


class CompressionLevel:
    """Compression levels for session history."""
    NONE = "none"           # Full conversations (< 7 days)
    LIGHT = "light"         # Q&A pairs + summary (7-30 days)
    MEDIUM = "medium"       # Summary only (30-90 days)
    HEAVY = "heavy"         # Learning profile only (> 90 days)


class HistoryManager:
    """Enhanced history manager with progressive compression and smart context detection."""
    
    def __init__(self, db: Database, llm_interface: LLMInterface):
        self.db = db
        self.llm = llm_interface
        self.context_detector = SmartContextDetector(llm_interface)
        self.history_dir = Path("user_history")
        self.history_dir.mkdir(exist_ok=True)
        
        # Compression schedule
        self.compression_schedule = {
            CompressionLevel.NONE: {"max_age_days": 7, "next_level": CompressionLevel.LIGHT},
            CompressionLevel.LIGHT: {"max_age_days": 30, "next_level": CompressionLevel.MEDIUM},
            CompressionLevel.MEDIUM: {"max_age_days": 90, "next_level": CompressionLevel.HEAVY},
            CompressionLevel.HEAVY: {"max_age_days": None, "next_level": None}
        }
        
        # Create compressed data directories
        self.compressed_dir = Path("user_history_compressed")
        self.compressed_dir.mkdir(exist_ok=True)
    
    def compress_session(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compress a conversation session into a summary.
        
        Args:
            conversations: List of conversation dictionaries with question/answer pairs
            
        Returns:
            Dictionary with compressed summary and metadata
        """
        if not conversations:
            return {
                "summary": "Empty session",
                "topics": [],
                "key_concepts": [],
                "question_count": 0
            }
        
        # Prepare conversation text for compression
        conversation_text = self._format_conversations_for_compression(conversations)
        
        # Use LLM to create summary
        prompt = f"""Analyze this educational conversation session and create a comprehensive summary.

Conversation:
{conversation_text}

Create a JSON response with:
1. A concise summary (2-3 sentences) capturing the main topics discussed
2. List of main topics covered
3. Key concepts or learning points extracted
4. Total number of questions asked

Format as:
{{
    "summary": "Brief summary text...",
    "topics": ["topic1", "topic2", ...],
    "key_concepts": ["concept1", "concept2", ...],
    "question_count": number
}}"""

        try:
            response = self.llm.generate_response(prompt, max_tokens=500)
            
            # Try to parse JSON
            import json
            summary_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["summary", "topics", "key_concepts", "question_count"]
            for field in required_fields:
                if field not in summary_data:
                    raise ValueError(f"Missing field: {field}")
            
            return summary_data
            
        except Exception as e:
            logger.warning(f"LLM compression failed, using fallback: {e}")
            # Fallback compression
            topics = self._extract_topics_fallback(conversations)
            return {
                "summary": f"Educational session covering {len(topics)} topics with {len(conversations)} questions",
                "topics": topics,
                "key_concepts": topics[:5],  # Use first 5 topics as key concepts
                "question_count": len(conversations)
            }

    def save_session_history(self, user_id: int, session_id: str, 
                           conversations: List[Dict[str, Any]], 
                           start_time: datetime, end_time: datetime):
        """
        Save session history with automatic compression based on age.
        """
        try:
            # Convert datetime objects to strings
            def convert_datetime(obj):
                if isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            # Convert conversations
            converted_conversations = convert_datetime(conversations)
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "conversations": converted_conversations,
                "compression_level": CompressionLevel.NONE,
                "created_at": datetime.now().isoformat()
            }
            
            # Create user directory if it doesn't exist
            user_dir = self.history_dir / str(user_id)
            user_dir.mkdir(exist_ok=True)
            
            # Save to JSON file
            session_file = user_dir / f"session_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved session history for user {user_id}: {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session history: {e}")

    def get_recent_history(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation summaries for a user."""
        try:
            user_dir = self.history_dir / str(user_id)
            if not user_dir.exists():
                return []
            
            # Get all session files, sorted by modification time (newest first)
            session_files = sorted(
                user_dir.glob("session_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            summaries = []
            for session_file in session_files[:limit]:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # Create summary for this session
                    summary = self.compress_session(session_data.get('conversations', []))
                    summary['session_id'] = session_data.get('session_id')
                    summary['date'] = session_data.get('start_time', '')[:10]  # Just the date part
                    
                    summaries.append(summary)
                except Exception as e:
                    logger.warning(f"Failed to process session file {session_file}: {e}")
                    continue
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to get recent history for user {user_id}: {e}")
            return []

    def get_full_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full session data for a specific session."""
        try:
            user_dir = self.history_dir / str(user_id)
            if not user_dir.exists():
                return None
            
            # Find session file by session_id
            for session_file in user_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    if session_data.get('session_id') == session_id:
                        return session_data
                        
                except Exception as e:
                    logger.warning(f"Failed to read session file {session_file}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id} for user {user_id}: {e}")
            return None

    def format_history_context(self, history_summaries: List[Dict[str, Any]]) -> str:
        """Format history summaries into context for the LLM."""
        if not history_summaries:
            return ""
        
        context_parts = ["Previous conversation context:"]
        
        for i, summary in enumerate(history_summaries):
            context_parts.append(f"\nSession {i+1} ({summary.get('date', 'Unknown date')}):")
            context_parts.append(f"  Summary: {summary.get('summary', 'No summary')}")
            
            if summary.get('topics'):
                context_parts.append(f"  Topics: {', '.join(summary['topics'][:3])}")  # First 3 topics
            
            if summary.get('key_concepts'):
                context_parts.append(f"  Key concepts: {', '.join(summary['key_concepts'][:3])}")  # First 3 concepts
        
        context_parts.append("\n")
        return "\n".join(context_parts)

    def should_include_history(self, question: str, user_id: int) -> Tuple[bool, str]:
        """
        Determine if historical context should be included for this question.
        Returns (should_include, reason)
        """
        should_fetch, confidence, reason = self.context_detector.should_fetch_history(
            question, user_id, self.db
        )
        
        # Only include history if we're confident it's needed
        if should_fetch and confidence > 0.6:
            return True, reason
        else:
            return False, f"Low confidence or no context needed: {reason}"

    def _format_conversations_for_compression(self, conversations: List[Dict[str, Any]]) -> str:
        """Format conversations for LLM compression."""
        formatted = []
        for i, conv in enumerate(conversations, 1):
            question = conv.get('question', 'No question')
            answer = conv.get('answer', 'No answer')
            
            # Truncate very long answers for compression
            if len(answer) > 1000:
                answer = answer[:1000] + "..."
            
            formatted.append(f"Q{i}: {question}")
            formatted.append(f"A{i}: {answer}")
            formatted.append("")  # Empty line between conversations
        
        return "\n".join(formatted)

    def _extract_topics_fallback(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """Extract topics using simple keyword analysis as fallback."""
        topics = set()
        
        for conv in conversations:
            question = conv.get('question', '').lower()
            answer = conv.get('answer', '').lower()
            
            # Simple keyword extraction
            text = f"{question} {answer}"
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)  # Words with 4+ characters
            
            # Filter common words and add to topics
            common_words = {'what', 'how', 'why', 'when', 'where', 'who', 'this', 'that', 'they', 'them', 'with', 'from', 'have', 'will', 'would', 'could', 'should'}
            topics.update(word for word in words if word not in common_words)
        
        return list(topics)[:10]  # Return first 10 topics

    def compress_old_sessions(self, user_id: int = None) -> Dict[str, int]:
        """
        Compress old sessions based on age and compression schedule.
        
        Args:
            user_id: If provided, only compress sessions for this user
            
        Returns:
            Dictionary with compression statistics
        """
        stats = {
            "sessions_processed": 0,
            "light_compression": 0,
            "medium_compression": 0,
            "heavy_compression": 0,
            "errors": 0
        }
        
        try:
            # Get user directories to process
            if user_id:
                user_dirs = [self.history_dir / str(user_id)]
            else:
                user_dirs = [d for d in self.history_dir.iterdir() if d.is_dir()]
            
            current_time = datetime.now()
            
            for user_dir in user_dirs:
                if not user_dir.exists():
                    continue
                
                # Process each session file
                for session_file in user_dir.glob("session_*.json"):
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        # Get session age
                        session_start = datetime.fromisoformat(session_data.get('start_time', ''))
                        age_days = (current_time - session_start).days
                        
                        current_level = session_data.get('compression_level', CompressionLevel.NONE)
                        
                        # Determine if compression is needed
                        schedule = self.compression_schedule.get(current_level)
                        if not schedule:
                            continue
                        
                        max_age = schedule.get('max_age_days')
                        next_level = schedule.get('next_level')
                        
                        if max_age and age_days > max_age and next_level:
                            # Compress to next level
                            compressed_data = self._compress_session_to_next_level(
                                session_data, current_level, next_level
                            )
                            
                            # Save compressed data
                            self._save_compressed_data(
                                int(user_dir.name), 
                                session_data['session_id'], 
                                compressed_data, 
                                next_level
                            )
                            
                            # Update statistics
                            stats["sessions_processed"] += 1
                            if next_level == CompressionLevel.LIGHT:
                                stats["light_compression"] += 1
                            elif next_level == CompressionLevel.MEDIUM:
                                stats["medium_compression"] += 1
                            elif next_level == CompressionLevel.HEAVY:
                                stats["heavy_compression"] += 1
                            
                            # Remove original file if heavily compressed
                            if next_level == CompressionLevel.HEAVY:
                                session_file.unlink()
                            
                    except Exception as e:
                        logger.error(f"Error processing session {session_file}: {e}")
                        stats["errors"] += 1
            
            logger.info(f"Compression cycle completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error in compression cycle: {e}")
            stats["errors"] += 1
        
        return stats

    def _compress_session_to_next_level(self, session: Dict, current_level: str, 
                                      next_level: str) -> Dict[str, Any]:
        """Compress session data to the next compression level."""
        
        if next_level == CompressionLevel.LIGHT:
            return self._light_compression(session)
        elif next_level == CompressionLevel.MEDIUM:
            return self._medium_compression(session)
        elif next_level == CompressionLevel.HEAVY:
            return self._heavy_compression(session)
        else:
            return session

    def _light_compression(self, session_data: Dict) -> Dict:
        """
        Light compression: Keep important Q&A pairs + create summary.
        Good for 7-30 day old sessions.
        """
        conversations = session_data.get('conversations', [])
        
        # Extract important Q&A pairs (longer questions/answers, educational content)
        important_qa = self._extract_important_qa(session_data)
        
        # Create session summary
        summary = self.compress_session(conversations)
        
        compressed = {
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
            "start_time": session_data['start_time'],
            "end_time": session_data['end_time'],
            "compression_level": CompressionLevel.LIGHT,
            "compressed_at": datetime.now().isoformat(),
            "summary": summary,
            "important_qa": important_qa,
            "original_question_count": len(conversations)
        }
        
        return compressed

    def _medium_compression(self, session_data: Dict) -> Dict:
        """
        Medium compression: Summary only, no individual Q&A.
        Good for 30-90 day old sessions.
        """
        conversations = session_data.get('conversations', [])
        summary = self.compress_session(conversations)
        
        compressed = {
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
            "start_time": session_data['start_time'],
            "end_time": session_data['end_time'],
            "compression_level": CompressionLevel.MEDIUM,
            "compressed_at": datetime.now().isoformat(),
            "summary": summary,
            "original_question_count": len(conversations)
        }
        
        return compressed

    def _heavy_compression(self, session_data: Dict) -> Dict:
        """
        Heavy compression: Extract learning profile data only.
        Good for >90 day old sessions.
        """
        learning_outcomes = self._extract_learning_outcomes(session_data)
        session_insights = self._extract_session_insights(session_data)
        
        compressed = {
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
            "start_time": session_data['start_time'],
            "compression_level": CompressionLevel.HEAVY,
            "compressed_at": datetime.now().isoformat(),
            "learning_outcomes": learning_outcomes,
            "session_insights": session_insights,
            "original_question_count": len(session_data.get('conversations', []))
        }
        
        return compressed

    def _summarize_answer(self, question: str, answer: str) -> str:
        """Create a brief summary of a Q&A pair."""
        try:
            prompt = f"""Summarize this educational Q&A in 1-2 sentences:

Q: {question}
A: {answer[:500]}...

Summary:"""
            
            summary = self.llm.generate_response(prompt, max_tokens=100)
            return summary.strip()
            
        except Exception:
            # Fallback to simple truncation
            return answer[:200] + "..." if len(answer) > 200 else answer

    def _extract_important_qa(self, session_data: Dict) -> List[Dict]:
        """Extract the most important Q&A pairs from a session."""
        conversations = session_data.get('conversations', [])
        
        # Score conversations based on length and content
        scored_conversations = []
        for conv in conversations:
            question = conv.get('question', '')
            answer = conv.get('answer', '')
            
            # Simple scoring: longer content = more important
            score = len(question) + len(answer)
            
            # Boost score for educational keywords
            educational_keywords = ['explain', 'how', 'why', 'what', 'example', 'definition', 'concept']
            for keyword in educational_keywords:
                if keyword in question.lower():
                    score += 100
            
            scored_conversations.append({
                'conversation': conv,
                'score': score
            })
        
        # Sort by score and take top 5
        sorted_convs = sorted(scored_conversations, key=lambda x: x['score'], reverse=True)
        
        important_qa = []
        for item in sorted_convs[:5]:  # Keep top 5 Q&A pairs
            conv = item['conversation']
            
            # Create summarized version
            summarized = {
                'question': conv.get('question', ''),
                'answer_summary': self._summarize_answer(
                    conv.get('question', ''), 
                    conv.get('answer', '')
                ),
                'timestamp': conv.get('timestamp', ''),
                'importance_score': item['score']
            }
            
            important_qa.append(summarized)
        
        return important_qa

    def _extract_learning_outcomes(self, session_data: Dict) -> List[str]:
        """Extract learning outcomes from a session."""
        conversations = session_data.get('conversations', [])
        
        try:
            # Prepare text for analysis
            session_text = self._format_conversations_for_compression(conversations)
            
            prompt = f"""Analyze this educational session and extract 3-5 key learning outcomes - what the student learned or understood.

Session:
{session_text[:2000]}...

Learning outcomes (one per line):
1. 
2. 
3. """
            
            response = self.llm.generate_response(prompt, max_tokens=300)
            
            # Extract numbered outcomes
            outcomes = []
            for line in response.split('\n'):
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    outcome = re.sub(r'^\d+\.\s*', '', line)
                    if outcome:
                        outcomes.append(outcome)
            
            return outcomes[:5]  # Limit to 5 outcomes
            
        except Exception as e:
            logger.warning(f"Failed to extract learning outcomes: {e}")
            return ["Session completed with educational content"]

    def _extract_session_insights(self, session_data: Dict) -> Dict:
        """Extract insights about the learning session."""
        conversations = session_data.get('conversations', [])
        
        insights = {
            "session_duration_minutes": self._calculate_session_duration(session_data),
            "question_count": len(conversations),
            "complexity_level": self._estimate_complexity(session_data),
            "session_type": self._classify_session_type(session_data),
            "topics_explored": len(set(self._extract_topics_fallback(conversations)))
        }
        
        return insights

    def _estimate_complexity(self, session_data: Dict) -> str:
        """Estimate the complexity level of the session."""
        conversations = session_data.get('conversations', [])
        
        # Simple heuristics for complexity
        avg_question_length = sum(len(c.get('question', '')) for c in conversations) / max(len(conversations), 1)
        avg_answer_length = sum(len(c.get('answer', '')) for c in conversations) / max(len(conversations), 1)
        
        if avg_question_length > 100 or avg_answer_length > 1000:
            return "high"
        elif avg_question_length > 50 or avg_answer_length > 500:
            return "medium"
        else:
            return "low"

    def _classify_session_type(self, session_data: Dict) -> str:
        """Classify the type of learning session."""
        conversations = session_data.get('conversations', [])
        
        # Analyze question patterns
        question_text = ' '.join(c.get('question', '') for c in conversations).lower()
        
        if any(word in question_text for word in ['solve', 'calculate', 'problem', 'equation']):
            return "problem_solving"
        elif any(word in question_text for word in ['explain', 'what is', 'how does', 'definition']):
            return "conceptual_learning"
        elif any(word in question_text for word in ['example', 'show me', 'demonstrate']):
            return "example_based"
        else:
            return "general_inquiry"

    def _calculate_session_duration(self, session_data: Dict) -> float:
        """Calculate session duration in minutes."""
        try:
            start_time = datetime.fromisoformat(session_data.get('start_time', ''))
            end_time = datetime.fromisoformat(session_data.get('end_time', ''))
            duration = (end_time - start_time).total_seconds() / 60
            return round(duration, 2)
        except:
            return 0.0

    def _save_compressed_data(self, user_id: int, session_id: str, 
                            compressed_data: Dict, compression_level: str):
        """Save compressed session data."""
        try:
            # Create user directory in compressed storage
            user_compressed_dir = self.compressed_dir / str(user_id)
            user_compressed_dir.mkdir(exist_ok=True)
            
            # Save compressed data
            filename = f"{session_id}_{compression_level}.json"
            filepath = user_compressed_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(compressed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {compression_level} compressed data: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save compressed data: {e}")

    def _update_learning_profile(self, user_id: int):
        """Update user's learning profile based on compressed session data."""
        try:
            # Get all compressed session data for user
            user_compressed_dir = self.compressed_dir / str(user_id)
            if not user_compressed_dir.exists():
                return
            
            learning_data = []
            for compressed_file in user_compressed_dir.glob("*_heavy.json"):
                try:
                    with open(compressed_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    learning_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to read compressed file {compressed_file}: {e}")
            
            if not learning_data:
                return
            
            # Aggregate learning profile
            profile = {
                "total_sessions": len(learning_data),
                "total_questions": sum(d.get('original_question_count', 0) for d in learning_data),
                "learning_outcomes": [],
                "preferred_complexity": self._infer_learning_style(learning_data),
                "common_session_types": [],
                "updated_at": datetime.now().isoformat()
            }
            
            # Collect all learning outcomes
            for session in learning_data:
                outcomes = session.get('learning_outcomes', [])
                profile['learning_outcomes'].extend(outcomes)
            
            # Save learning profile
            profile_file = user_compressed_dir / "learning_profile.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated learning profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update learning profile for user {user_id}: {e}")

    def _infer_learning_style(self, sessions: List[Dict]) -> str:
        """Infer learning style from session patterns."""
        if not sessions:
            return "unknown"
        
        complexity_counts = {}
        for session in sessions:
            insights = session.get('session_insights', {})
            complexity = insights.get('complexity_level', 'unknown')
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        # Return most common complexity level
        if complexity_counts:
            return max(complexity_counts, key=complexity_counts.get)
        else:
            return "unknown"

    def get_compressed_session_data(self, user_id: int, session_id: str) -> Optional[Dict]:
        """Get compressed session data for a specific session."""
        try:
            user_compressed_dir = self.compressed_dir / str(user_id)
            if not user_compressed_dir.exists():
                return None
            
            # Look for compressed files with this session_id
            for compressed_file in user_compressed_dir.glob(f"{session_id}_*.json"):
                try:
                    with open(compressed_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read compressed file {compressed_file}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get compressed session data: {e}")
            return None

    def run_compression_cycle(self) -> Dict[str, int]:
        """Run a compression cycle for all users."""
        try:
            stats = self.compress_old_sessions()
            
            # Update learning profiles for users with heavily compressed sessions
            if stats["heavy_compression"] > 0:
                for user_dir in self.compressed_dir.iterdir():
                    if user_dir.is_dir() and user_dir.name.isdigit():
                        self._update_learning_profile(int(user_dir.name))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in compression cycle: {e}")
            return {"errors": 1}
