"""
Content management module for handling class, subject, and textbook data.
"""

import os
import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentManager:
    """Manages educational content structure and database population."""
    
    def __init__(self, db: Database = None):
        """Initialize content manager."""
        self.db = db or Database()
        self.ncert_base_path = "NCERT_Textbooks"
    
    def parse_ncert_directory(self, base_path: str = None) -> Dict:
        """
        Parse NCERT textbooks directory structure and return mapping.
        Structure expected: NCERT_Textbooks/class[1-10]/subject/textbook_files
        """
        base_path = base_path or self.ncert_base_path
        
        if not os.path.exists(base_path):
            logger.error(f"Directory not found: {base_path}")
            return {}
        
        structure = {
            'classes': {},
            'total_textbooks': 0,
            'errors': []
        }
        
        # Parse directory structure
        try:
            for class_dir in os.listdir(base_path):
                class_path = os.path.join(base_path, class_dir)
                
                # Check if it's a class directory (class1, class2, etc.)
                if not os.path.isdir(class_path) or not class_dir.startswith('class'):
                    continue
                
                class_match = re.match(r'class(\d+)', class_dir)
                if not class_match:
                    continue
                
                class_num = int(class_match.group(1))
                if class_num < 1 or class_num > 10:
                    continue
                
                class_name = class_dir.lower()
                structure['classes'][class_name] = {
                    'display_name': f"Class {class_num}",
                    'order': class_num,
                    'subjects': {}
                }
                
                # Parse subjects in this class
                for subject_dir in os.listdir(class_path):
                    subject_path = os.path.join(class_path, subject_dir)
                    
                    if not os.path.isdir(subject_path):
                        continue
                    
                    # Normalize subject name
                    subject_name = self.normalize_subject_name(subject_dir)
                    
                    structure['classes'][class_name]['subjects'][subject_name] = {
                        'original_name': subject_dir,
                        'textbooks': []
                    }
                    
                    # Each subdirectory in subject folder is a textbook
                    # e.g., class1/english/marigold where marigold is the textbook
                    for textbook_dir in os.listdir(subject_path):
                        textbook_path = os.path.join(subject_path, textbook_dir)
                        
                        if not os.path.isdir(textbook_path):
                            continue
                        
                        # The directory name is the textbook name
                        textbook_name = self.normalize_textbook_name(textbook_dir)
                        
                        # Find all chapter PDFs in this textbook directory
                        chapter_files = self.find_chapters_in_textbook(textbook_path)
                        
                        if chapter_files:
                            # Create a single textbook entry that represents all chapters
                            structure['classes'][class_name]['subjects'][subject_name]['textbooks'].append({
                                'name': textbook_name,
                                'file_path': textbook_path,  # Store the directory path
                                'file_name': textbook_dir,
                                'chapters': chapter_files,
                                'chapter_count': len(chapter_files)
                            })
                            structure['total_textbooks'] += 1
        
        except Exception as e:
            logger.error(f"Error parsing directory: {e}")
            structure['errors'].append(str(e))
        
        return structure
    
    def normalize_subject_name(self, subject_dir: str) -> str:
        """Normalize subject directory name to standard format."""
        # Remove hyphens and underscores, convert to title case
        normalized = subject_dir.replace('-', ' ').replace('_', ' ')
        normalized = ' '.join(word.capitalize() for word in normalized.split())
        
        # Map common variations
        subject_mapping = {
            'maths': 'Mathematics',
            'math': 'Mathematics',
            'science': 'Science',
            'english': 'English',
            'hindi': 'Hindi',
            'social': 'Social Studies',
            'social science': 'Social Studies',
            'social studies': 'Social Studies',
            'evs': 'Environmental Studies',
            'environmental studies': 'Environmental Studies',
            'environmental science': 'Environmental Studies',
            'geography': 'Geography',
            'history': 'History',
            'civics': 'Civics',
            'economics': 'Economics',
            'political science': 'Political Science'
        }
        
        lower_normalized = normalized.lower()
        for key, value in subject_mapping.items():
            if key in lower_normalized:
                return value
        
        return normalized
    
    def normalize_textbook_name(self, textbook_dir: str) -> str:
        """Normalize textbook directory name to readable format."""
        # Replace hyphens and underscores with spaces
        name = textbook_dir.replace('-', ' ').replace('_', ' ')
        
        # Clean up multiple spaces
        name = ' '.join(name.split())
        
        # Convert to proper/title case
        # Handle special words that should remain lowercase
        articles = ['a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
        words = name.split()
        
        # Always capitalize the first word
        if words:
            words[0] = words[0].capitalize()
        
        # Process remaining words
        for i in range(1, len(words)):
            if words[i].lower() in articles:
                words[i] = words[i].lower()
            else:
                words[i] = words[i].capitalize()
        
        name = ' '.join(words)
        
        # Special cases for known textbook names (after processing)
        textbook_mapping = {
            'joyful mathematics english': 'Joyful Mathematics',
            'joyful mathematics': 'Joyful Mathematics',
            'math magic': 'Math Magic',
            'math mela': 'Math Mela',
            'maths mela': 'Maths Mela',
            'marigold': 'Marigold',
            'mridang': 'Mridang',
            'santoor': 'Santoor'
        }
        
        lower_name = name.lower()
        for key, value in textbook_mapping.items():
            if lower_name == key:
                return value
        
        return name
    
    def find_chapters_in_textbook(self, textbook_path: str) -> List[Dict]:
        """Find all chapter PDF files in a textbook directory."""
        chapters = []
        
        try:
            for filename in os.listdir(textbook_path):
                file_path = os.path.join(textbook_path, filename)
                
                # Skip non-PDF files and directories
                if not filename.lower().endswith('.pdf'):
                    continue
                
                # Skip title.pdf and zip files
                if filename.lower() in ['title.pdf'] or filename.lower().endswith('.zip'):
                    continue
                
                # Extract chapter information
                chapter_info = self.extract_chapter_info(filename)
                chapters.append({
                    'filename': filename,
                    'file_path': file_path,
                    'chapter_name': chapter_info['name'],
                    'chapter_number': chapter_info['number'],
                    'is_complete': chapter_info['is_complete']
                })
            
            # Sort chapters by number (complete book last)
            chapters.sort(key=lambda x: (x['is_complete'], x['chapter_number'] or 999))
            
        except Exception as e:
            logger.error(f"Error reading textbook directory {textbook_path}: {e}")
        
        return chapters
    
    def extract_chapter_info(self, filename: str) -> Dict:
        """Extract chapter information from filename."""
        name = os.path.splitext(filename)[0]
        
        # Check for complete book (ends with 'cc')
        if name.endswith('cc'):
            return {
                'name': 'Complete Book',
                'number': None,
                'is_complete': True
            }
        
        # Extract chapter number (last 2 digits)
        if len(name) >= 2 and name[-2:].isdigit():
            chapter_num = int(name[-2:])
            return {
                'name': f'Chapter {chapter_num}',
                'number': chapter_num,
                'is_complete': False
            }
        
        # Default case
        return {
            'name': name,
            'number': None,
            'is_complete': False
        }
    
    def find_textbooks_in_directory(self, directory: str) -> List[Dict]:
        """Find all textbook files in a directory."""
        textbooks = []
        
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Skip directories and non-PDF files
                if os.path.isdir(file_path) or not filename.lower().endswith('.pdf'):
                    continue
                
                # Skip title.pdf
                if filename.lower() == 'title.pdf':
                    continue
                
                # Extract textbook name from filename
                textbook_name = self.extract_textbook_name(filename)
                
                textbooks.append({
                    'name': textbook_name,
                    'file_name': filename,
                    'file_path': file_path
                })
        
        except Exception as e:
            logger.error(f"Error reading directory {directory}: {e}")
        
        # Sort textbooks by name
        textbooks.sort(key=lambda x: x['name'])
        
        return textbooks
    
    def extract_textbook_name(self, filename: str) -> str:
        """Extract readable textbook name from filename."""
        # Remove extension
        name = os.path.splitext(filename)[0]
        
        # Handle NCERT naming pattern (e.g., 'aemr101' -> 'Chapter 1')
        # Check if it ends with 2 digits
        if len(name) >= 2 and name[-2:].isdigit():
            chapter_num = int(name[-2:])
            if chapter_num > 0:
                return f"Chapter {chapter_num}"
        
        # Handle 'cc' suffix (e.g., 'aemr1cc' -> 'Complete Book')
        if name.endswith('cc'):
            return "Complete Book"
        
        # Default handling
        # Remove chapter numbers at the end
        name = re.sub(r'\d+$', '', name)
        
        # Replace underscores and hyphens with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Title case
        name = ' '.join(word.capitalize() for word in name.split())
        
        # Clean up multiple spaces
        name = ' '.join(name.split())
        
        return name.strip() or filename
    
    def populate_database(self, structure: Dict = None) -> Dict:
        """Populate database with parsed structure."""
        if structure is None:
            structure = self.parse_ncert_directory()
        
        if not structure or not structure['classes']:
            return {
                'success': False,
                'error': 'No content structure provided or found',
                'stats': {}
            }
        
        stats = {
            'classes_added': 0,
            'subjects_added': 0,
            'textbooks_added': 0,
            'errors': []
        }
        
        try:
            # Add classes
            for class_name, class_data in structure['classes'].items():
                try:
                    # Check if class exists
                    existing_class = self.db.get_class_by_name(class_name)
                    if not existing_class:
                        class_id = self.db.create_class(class_name, class_data['order'])
                        stats['classes_added'] += 1
                        logger.info(f"Added class: {class_name}")
                    else:
                        class_id = existing_class['id']
                        logger.info(f"Class already exists: {class_name}")
                    
                    # Add subjects for this class
                    for subject_name, subject_data in class_data['subjects'].items():
                        try:
                            # Check if subject exists for this class
                            existing_subjects = self.db.get_subjects_by_class(class_id)
                            subject_exists = any(s['subject_name'] == subject_name for s in existing_subjects)
                            
                            if not subject_exists:
                                subject_id = self.db.create_subject(subject_name, class_id)
                                stats['subjects_added'] += 1
                                logger.info(f"Added subject: {subject_name} for {class_name}")
                            else:
                                subject_id = next(s['id'] for s in existing_subjects if s['subject_name'] == subject_name)
                                logger.info(f"Subject already exists: {subject_name} for {class_name}")
                            
                            # Add textbooks for this subject
                            for textbook in subject_data['textbooks']:
                                try:
                                    # Check if textbook already exists
                                    existing_textbooks = self.db.get_textbooks_by_subject(subject_id)
                                    textbook_exists = any(
                                        t['file_path'] == textbook['file_path'] 
                                        for t in existing_textbooks
                                    )
                                    
                                    if not textbook_exists:
                                        metadata = {
                                            'directory_name': textbook['file_name'],
                                            'class': class_name,
                                            'subject': subject_name,
                                            'chapters': textbook.get('chapters', []),
                                            'chapter_count': textbook.get('chapter_count', 0)
                                        }
                                        
                                        self.db.create_textbook(
                                            book_name=textbook['name'],
                                            file_path=textbook['file_path'],  # This is the directory path
                                            subject_id=subject_id,
                                            metadata=metadata
                                        )
                                        stats['textbooks_added'] += 1
                                        logger.info(f"Added textbook: {textbook['name']} ({textbook.get('chapter_count', 0)} chapters)")
                                    else:
                                        logger.info(f"Textbook already exists: {textbook['name']}")
                                
                                except Exception as e:
                                    error_msg = f"Error adding textbook {textbook['name']}: {e}"
                                    logger.error(error_msg)
                                    stats['errors'].append(error_msg)
                        
                        except Exception as e:
                            error_msg = f"Error adding subject {subject_name}: {e}"
                            logger.error(error_msg)
                            stats['errors'].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error adding class {class_name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            return {
                'success': True,
                'stats': stats
            }
        
        except Exception as e:
            logger.error(f"Database population error: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': stats
            }
    
    def get_content_summary(self) -> Dict:
        """Get summary of all content in database."""
        summary = {
            'classes': [],
            'total_subjects': 0,
            'total_textbooks': 0
        }
        
        classes = self.db.get_all_classes()
        
        for class_data in classes:
            class_info = {
                'id': class_data['id'],
                'name': class_data['class_name'],
                'display_name': class_data['class_name'].replace('class', 'Class '),
                'subjects': []
            }
            
            subjects = self.db.get_subjects_by_class(class_data['id'])
            
            for subject in subjects:
                subject_info = {
                    'id': subject['id'],
                    'name': subject['subject_name'],
                    'textbook_count': 0,
                    'textbooks': []
                }
                
                textbooks = self.db.get_textbooks_by_subject(subject['id'])
                subject_info['textbook_count'] = len(textbooks)
                subject_info['textbooks'] = [
                    {
                        'id': t['id'],
                        'name': t['book_name'],
                        'file_path': t['file_path']
                    }
                    for t in textbooks
                ]
                
                class_info['subjects'].append(subject_info)
                summary['total_textbooks'] += len(textbooks)
            
            summary['total_subjects'] += len(subjects)
            summary['classes'].append(class_info)
        
        return summary
    
    def initialize_content(self) -> Dict:
        """Initialize database with NCERT content if not already present."""
        # Check if content already exists
        classes = self.db.get_all_classes()
        if classes:
            logger.info("Content already initialized")
            return {
                'success': True,
                'message': 'Content already initialized',
                'stats': {
                    'existing_classes': len(classes)
                }
            }
        
        # Parse and populate
        logger.info("Initializing content from NCERT directory...")
        structure = self.parse_ncert_directory()
        
        if not structure or not structure['classes']:
            return {
                'success': False,
                'error': 'No NCERT content found'
            }
        
        result = self.populate_database(structure)
        
        if result['success']:
            logger.info("Content initialization completed successfully")
        else:
            logger.error("Content initialization failed")
        
        return result
