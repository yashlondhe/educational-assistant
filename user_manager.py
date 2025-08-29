"""
User management module for handling user profiles and selections.
"""

from typing import Dict, List, Optional
import logging

from database import Database
from auth import AuthManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManager:
    """Manages user profiles and their educational content selections."""
    
    def __init__(self, db: Database = None):
        """Initialize user manager."""
        self.db = db or Database()
        self.auth_manager = AuthManager(self.db)
    
    def get_user_full_info(self, user_id: int) -> Optional[Dict]:
        """Get complete user information including selections."""
        user_info = self.auth_manager.get_user_info(user_id)
        if not user_info:
            return None
        
        # Add current selections
        subject_selection = self.db.get_user_subject_selection(user_id)
        selected_textbooks = self.db.get_user_selected_textbooks(user_id)
        
        user_info['current_subject'] = subject_selection
        user_info['selected_textbooks'] = selected_textbooks
        
        return user_info
    
    def get_user_class_info(self, user_id: int) -> Optional[Dict]:
        """Get user's class information."""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return None
        
        # Get class details
        class_info = self.db.get_class_by_name(profile['class_grade'])
        if not class_info:
            logger.warning(f"Class {profile['class_grade']} not found in database")
            return {
                'class_name': profile['class_grade'],
                'class_id': None,
                'display_name': profile['class_grade'].replace('class', 'Class ')
            }
        
        return {
            'class_name': class_info['class_name'],
            'class_id': class_info['id'],
            'display_name': class_info['class_name'].replace('class', 'Class ')
        }
    
    def get_available_subjects(self, user_id: int) -> List[Dict]:
        """Get available subjects for user's class."""
        class_info = self.get_user_class_info(user_id)
        if not class_info or not class_info['class_id']:
            return []
        
        subjects = self.db.get_subjects_by_class(class_info['class_id'])
        
        # Add selection status
        current_selection = self.db.get_user_subject_selection(user_id)
        current_subject_id = current_selection['subject_id'] if current_selection else None
        
        for subject in subjects:
            subject['is_selected'] = subject['id'] == current_subject_id
        
        return subjects
    
    def select_subject(self, user_id: int, subject_id: int) -> bool:
        """Select a subject for the user."""
        # Verify subject belongs to user's class
        class_info = self.get_user_class_info(user_id)
        if not class_info or not class_info['class_id']:
            logger.error(f"No class found for user {user_id}")
            return False
        
        subjects = self.db.get_subjects_by_class(class_info['class_id'])
        subject_ids = [s['id'] for s in subjects]
        
        if subject_id not in subject_ids:
            logger.error(f"Subject {subject_id} not available for user's class")
            return False
        
        try:
            self.db.save_user_subject_selection(user_id, subject_id)
            # Clear textbook selections when subject changes
            self.db.save_user_textbook_selections(user_id, [])
            return True
        except Exception as e:
            logger.error(f"Error selecting subject: {e}")
            return False
    
    def get_available_textbooks(self, user_id: int) -> List[Dict]:
        """Get available textbooks for user's selected subject."""
        current_selection = self.db.get_user_subject_selection(user_id)
        if not current_selection:
            return []
        
        textbooks = self.db.get_textbooks_by_subject(current_selection['subject_id'])
        
        # Add selection status
        selected_textbooks = self.db.get_user_selected_textbooks(user_id)
        selected_ids = [t['id'] for t in selected_textbooks]
        
        for textbook in textbooks:
            textbook['is_selected'] = textbook['id'] in selected_ids
        
        return textbooks
    
    def select_textbooks(self, user_id: int, textbook_ids: List[int]) -> bool:
        """Select textbooks for the user."""
        if not textbook_ids:
            logger.error("At least one textbook must be selected")
            return False
        
        # Verify textbooks belong to user's selected subject
        current_selection = self.db.get_user_subject_selection(user_id)
        if not current_selection:
            logger.error(f"No subject selected for user {user_id}")
            return False
        
        available_textbooks = self.db.get_textbooks_by_subject(current_selection['subject_id'])
        available_ids = [t['id'] for t in available_textbooks]
        
        # Check all selected textbooks are valid
        for textbook_id in textbook_ids:
            if textbook_id not in available_ids:
                logger.error(f"Textbook {textbook_id} not available for selected subject")
                return False
        
        try:
            self.db.save_user_textbook_selections(user_id, textbook_ids)
            return True
        except Exception as e:
            logger.error(f"Error selecting textbooks: {e}")
            return False
    
    def get_selection_summary(self, user_id: int) -> Dict:
        """Get summary of user's current selections."""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return {}
        
        subject_selection = self.db.get_user_subject_selection(user_id)
        selected_textbooks = self.db.get_user_selected_textbooks(user_id)
        
        summary = {
            'class': profile['class_grade'].replace('class', 'Class '),
            'subject': None,
            'textbooks': [],
            'textbook_count': 0
        }
        
        if subject_selection:
            summary['subject'] = subject_selection['subject_name']
            
        if selected_textbooks:
            summary['textbooks'] = [t['book_name'] for t in selected_textbooks]
            summary['textbook_count'] = len(selected_textbooks)
        
        return summary
    
    def validate_user_selections(self, user_id: int) -> Dict:
        """Validate that user has made all required selections."""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if user has selected a subject
        subject_selection = self.db.get_user_subject_selection(user_id)
        if not subject_selection:
            validation['is_valid'] = False
            validation['errors'].append("No subject selected. Please select a subject.")
            return validation
        
        # Check if user has selected at least one textbook
        selected_textbooks = self.db.get_user_selected_textbooks(user_id)
        if not selected_textbooks:
            validation['is_valid'] = False
            validation['errors'].append("No textbooks selected. Please select at least one textbook.")
            return validation
        
        # Check if selected textbooks exist
        textbook_paths = self.db.get_user_selected_textbook_paths(user_id)
        import os
        for path in textbook_paths:
            if not os.path.exists(path):
                validation['warnings'].append(f"Textbook file not found: {path}")
        
        return validation
