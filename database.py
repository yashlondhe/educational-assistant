"""
Database module for managing SQLite database connections and operations.
"""

import sqlite3
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Handles all database operations for the educational assistant."""
    
    def __init__(self, db_path: str = "educational_assistant.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    date_of_birth DATE,
                    phone_number TEXT,
                    class_grade TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT UNIQUE NOT NULL,
                    display_order INTEGER
                )
            """)
            
            # Subjects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT NOT NULL,
                    class_id INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                    UNIQUE(subject_name, class_id)
                )
            """)
            
            # Textbooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS textbooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    subject_id INTEGER NOT NULL,
                    metadata JSON,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            """)
            
            # User selections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                    UNIQUE(user_id)
                )
            """)
            
            # User selected textbooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_selected_textbooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    textbook_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (textbook_id) REFERENCES textbooks(id) ON DELETE CASCADE,
                    UNIQUE(user_id, textbook_id)
                )
            """)
            
            # User conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    compressed_summary TEXT NOT NULL,
                    question_count INTEGER DEFAULT 0,
                    topics TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    compression_level TEXT DEFAULT 'none',
                    key_concepts TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # User learning profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_learning_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    profile_data TEXT NOT NULL,
                    topic_mastery TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Session compression status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_compression_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    compression_level TEXT NOT NULL,
                    last_compressed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_class ON subjects(class_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_textbooks_subject ON textbooks(subject_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_selections_user ON user_selections(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_textbooks_user ON user_selected_textbooks(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_history ON user_conversation_history(user_id, timestamp DESC)")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def execute_insert(self, query: str, params: tuple) -> int:
        """Execute an INSERT query and return the last row ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_update(self, query: str, params: tuple) -> int:
        """Execute an UPDATE query and return the number of affected rows."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_delete(self, query: str, params: tuple) -> int:
        """Execute a DELETE query and return the number of affected rows."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # User-related methods
    def create_user(self, email: str, password_hash: str) -> int:
        """Create a new user."""
        query = "INSERT INTO users (email, password_hash) VALUES (?, ?)"
        return self.execute_insert(query, (email, password_hash))
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.execute_query(query, (email,))
        return results[0] if results else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = ?"
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        self.execute_update(query, (user_id,))
    
    # Profile-related methods
    def create_user_profile(self, user_id: int, name: str, class_grade: str, 
                          date_of_birth: str = None, phone_number: str = None) -> int:
        """Create user profile."""
        query = """
            INSERT INTO user_profiles (user_id, name, date_of_birth, phone_number, class_grade)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (user_id, name, date_of_birth, phone_number, class_grade))
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile by user ID."""
        query = "SELECT * FROM user_profiles WHERE user_id = ?"
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_user_profile(self, user_id: int, **kwargs) -> int:
        """Update user profile with provided fields."""
        allowed_fields = ['name', 'date_of_birth', 'phone_number', 'class_grade']
        update_fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return 0
        
        values.append(user_id)
        query = f"""
            UPDATE user_profiles 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """
        return self.execute_update(query, tuple(values))
    
    # Class/Subject/Textbook methods
    def create_class(self, class_name: str, display_order: int = None) -> int:
        """Create a new class."""
        query = "INSERT INTO classes (class_name, display_order) VALUES (?, ?)"
        return self.execute_insert(query, (class_name, display_order))
    
    def get_all_classes(self) -> List[Dict]:
        """Get all classes ordered by display_order."""
        query = "SELECT * FROM classes ORDER BY display_order, class_name"
        return self.execute_query(query)
    
    def get_class_by_name(self, class_name: str) -> Optional[Dict]:
        """Get class by name."""
        query = "SELECT * FROM classes WHERE class_name = ?"
        results = self.execute_query(query, (class_name,))
        return results[0] if results else None
    
    def create_subject(self, subject_name: str, class_id: int) -> int:
        """Create a new subject for a class."""
        query = "INSERT INTO subjects (subject_name, class_id) VALUES (?, ?)"
        return self.execute_insert(query, (subject_name, class_id))
    
    def get_subjects_by_class(self, class_id: int) -> List[Dict]:
        """Get all subjects for a class."""
        query = "SELECT * FROM subjects WHERE class_id = ? ORDER BY subject_name"
        return self.execute_query(query, (class_id,))
    
    def create_textbook(self, book_name: str, file_path: str, subject_id: int, metadata: Dict = None) -> int:
        """Create a new textbook."""
        metadata_json = json.dumps(metadata) if metadata else None
        query = "INSERT INTO textbooks (book_name, file_path, subject_id, metadata) VALUES (?, ?, ?, ?)"
        return self.execute_insert(query, (book_name, file_path, subject_id, metadata_json))
    
    def get_textbooks_by_subject(self, subject_id: int) -> List[Dict]:
        """Get all textbooks for a subject."""
        query = "SELECT * FROM textbooks WHERE subject_id = ? ORDER BY book_name"
        results = self.execute_query(query, (subject_id,))
        # Parse JSON metadata
        for result in results:
            if result['metadata']:
                result['metadata'] = json.loads(result['metadata'])
        return results
    
    # User selection methods
    def save_user_subject_selection(self, user_id: int, subject_id: int):
        """Save user's subject selection."""
        query = """
            INSERT INTO user_selections (user_id, subject_id) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) 
            DO UPDATE SET subject_id = ?, updated_at = CURRENT_TIMESTAMP
        """
        self.execute_insert(query, (user_id, subject_id, subject_id))
    
    def get_user_subject_selection(self, user_id: int) -> Optional[Dict]:
        """Get user's current subject selection."""
        query = """
            SELECT us.*, s.subject_name, s.class_id 
            FROM user_selections us
            JOIN subjects s ON us.subject_id = s.id
            WHERE us.user_id = ?
        """
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def save_user_textbook_selections(self, user_id: int, textbook_ids: List[int]):
        """Save user's textbook selections."""
        # First, clear existing selections
        self.execute_delete("DELETE FROM user_selected_textbooks WHERE user_id = ?", (user_id,))
        
        # Then insert new selections
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            for textbook_id in textbook_ids:
                cursor.execute(
                    "INSERT INTO user_selected_textbooks (user_id, textbook_id) VALUES (?, ?)",
                    (user_id, textbook_id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_user_selected_textbooks(self, user_id: int) -> List[Dict]:
        """Get user's selected textbooks."""
        query = """
            SELECT t.* 
            FROM textbooks t
            JOIN user_selected_textbooks ust ON t.id = ust.textbook_id
            WHERE ust.user_id = ?
            ORDER BY t.book_name
        """
        results = self.execute_query(query, (user_id,))
        # Parse JSON metadata
        for result in results:
            if result['metadata']:
                result['metadata'] = json.loads(result['metadata'])
        return results
    
    def get_user_selected_textbook_paths(self, user_id: int) -> List[str]:
        """Get file paths of user's selected textbooks (all chapter PDFs)."""
        textbooks = self.get_user_selected_textbooks(user_id)
        all_paths = []
        
        for book in textbooks:
            # The file_path is actually a directory path for the textbook
            if book['metadata'] and 'chapters' in book['metadata']:
                # Extract all chapter file paths
                for chapter in book['metadata']['chapters']:
                    if 'file_path' in chapter:
                        all_paths.append(chapter['file_path'])
            else:
                # Fallback: if no chapter info, use the directory path
                # This shouldn't happen with the new structure
                all_paths.append(book['file_path'])
        
        return all_paths
    
    # Conversation history methods
    def save_conversation_history(self, user_id: int, session_id: str, 
                                compressed_summary: str, question_count: int, 
                                topics: List[str], compression_level: str = 'none',
                                key_concepts: List[str] = None) -> int:
        """Save compressed conversation history."""
        topics_json = json.dumps(topics) if topics else None
        key_concepts_json = json.dumps(key_concepts) if key_concepts else None
        query = """
            INSERT INTO user_conversation_history 
            (user_id, session_id, compressed_summary, question_count, topics, 
             compression_level, key_concepts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (user_id, session_id, compressed_summary, 
                                          question_count, topics_json, 
                                          compression_level, key_concepts_json))
    
    def get_recent_conversation_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent conversation history for a user."""
        query = """
            SELECT * FROM user_conversation_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        results = self.execute_query(query, (user_id, limit))
        # Parse JSON fields
        for result in results:
            if result.get('topics'):
                result['topics'] = json.loads(result['topics'])
            if result.get('key_concepts'):
                result['key_concepts'] = json.loads(result['key_concepts'])
        return results
    
    def get_conversation_history_count(self, user_id: int) -> int:
        """Get total number of conversation histories for a user."""
        query = "SELECT COUNT(*) as count FROM user_conversation_history WHERE user_id = ?"
        results = self.execute_query(query, (user_id,))
        return results[0]['count'] if results else 0
    
    # Learning profile methods
    def save_or_update_learning_profile(self, user_id: int, profile_data: Dict, 
                                      topic_mastery: Dict) -> bool:
        """Save or update user learning profile."""
        profile_json = json.dumps(profile_data)
        mastery_json = json.dumps(topic_mastery)
        
        # Try update first
        query = """
            UPDATE user_learning_profiles 
            SET profile_data = ?, topic_mastery = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """
        rows_affected = self.execute_update(query, (profile_json, mastery_json, user_id))
        
        if rows_affected == 0:
            # Insert if no existing profile
            query = """
                INSERT INTO user_learning_profiles (user_id, profile_data, topic_mastery)
                VALUES (?, ?, ?)
            """
            self.execute_insert(query, (user_id, profile_json, mastery_json))
        
        return True
    
    def get_learning_profile(self, user_id: int) -> Optional[Dict]:
        """Get user learning profile."""
        query = "SELECT * FROM user_learning_profiles WHERE user_id = ?"
        results = self.execute_query(query, (user_id,))
        if results:
            result = results[0]
            result['profile_data'] = json.loads(result['profile_data'])
            result['topic_mastery'] = json.loads(result['topic_mastery']) if result['topic_mastery'] else {}
            return result
        return None
    
    # Compression status methods
    def save_compression_status(self, session_id: str, user_id: int, 
                              compression_level: str, file_path: str = None) -> int:
        """Save or update session compression status."""
        query = """
            INSERT INTO session_compression_status (session_id, user_id, compression_level, file_path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                compression_level = ?,
                last_compressed = CURRENT_TIMESTAMP,
                file_path = ?
        """
        return self.execute_insert(query, (session_id, user_id, compression_level, file_path,
                                         compression_level, file_path))
    
    def get_sessions_by_compression_level(self, user_id: int, compression_level: str) -> List[Dict]:
        """Get sessions by compression level."""
        query = """
            SELECT * FROM session_compression_status 
            WHERE user_id = ? AND compression_level = ?
            ORDER BY last_compressed DESC
        """
        return self.execute_query(query, (user_id, compression_level))
    
    def get_sessions_for_compression(self, older_than_days: int, 
                                   current_level: str = 'none') -> List[Dict]:
        """Get sessions that need compression based on age."""
        query = """
            SELECT h.*, s.compression_level, s.file_path
            FROM user_conversation_history h
            LEFT JOIN session_compression_status s ON h.session_id = s.session_id
            WHERE h.timestamp < datetime('now', '-' || ? || ' days')
            AND (s.compression_level IS NULL OR s.compression_level = ?)
            ORDER BY h.timestamp ASC
        """
        return self.execute_query(query, (older_than_days, current_level))
