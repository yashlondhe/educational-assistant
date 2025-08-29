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
            
            # Create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_class ON subjects(class_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_textbooks_subject ON textbooks(subject_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_selections_user ON user_selections(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_textbooks_user ON user_selected_textbooks(user_id)")
            
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
