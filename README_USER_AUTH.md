# User Authentication and Content Selection Enhancement

This document describes the new user authentication and content selection features added to the Educational Assistant.

## 🎯 New Features

### 1. User Authentication System
- **Registration**: Users can create accounts with email, password, and profile information
- **Login/Logout**: Secure authentication with session management
- **Profile Management**: Users can view and edit their profile details

### 2. User Profile
Users must provide:
- Email address (unique)
- Password (minimum 6 characters)
- Full name
- Class (1-10)
- Date of birth (optional)
- Phone number (optional)

### 3. Content Selection Hierarchy
- **Class-based Navigation**: Content is filtered based on user's class
- **Subject Selection**: Users select one subject at a time
- **Textbook Selection**: Users can select multiple textbooks within a subject
- **Mandatory Selection**: At least one subject and one textbook must be selected

### 4. Personalized Question Answering
- **Filtered Search**: Only searches within user's selected textbooks
- **Class-aware Responses**: LLM considers user's class level when generating answers
- **Selection Validation**: Ensures users have made valid selections before answering

## 🏗️ New Components

### Database Schema (`database.py`)
- SQLite database with tables for:
  - Users and authentication
  - User profiles
  - Classes, subjects, and textbooks
  - User selections

### Authentication (`auth.py`)
- User registration and login
- Password hashing (SHA-256 with salt)
- Email validation
- Profile updates

### User Management (`user_manager.py`)
- Subject and textbook selection
- Selection validation
- User information retrieval

### Content Management (`content_manager.py`)
- NCERT directory parsing
- Database population
- Content structure management

## 🚀 Setup Instructions

### 1. Initialize the Database
Run this once to set up the content structure:
```bash
python initialize_database.py
```

### 2. Run the New Streamlit App
```bash
streamlit run streamlit_app_new.py
```

### 3. Test the System
```bash
python test_system.py
```

## 📱 User Flow

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

4. **Profile Management**
   - Users can update their profile
   - Class changes affect available content

## 🔒 Security Features

- Password hashing (not stored in plain text)
- Session management
- Input validation
- SQL injection prevention

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
```

## 🧪 Testing

The `test_system.py` script tests:
1. Content initialization
2. User registration
3. Login functionality
4. Subject/textbook selection
5. Selection validation
6. Personalized Q&A
7. Profile updates

## 📝 Important Notes

1. **First Time Setup**: Run `initialize_database.py` to populate the content structure
2. **Vector Store**: The existing vector store must be populated separately
3. **Class Changes**: If a user changes their class, they need to reselect subject and textbooks
4. **Selection Persistence**: User selections are saved in the database

## 🔄 Migration from Old System

The new system is backward compatible:
- Existing vector stores continue to work
- Old CLI and Streamlit apps remain functional
- New features are in `streamlit_app_new.py`

## 📈 Future Enhancements

1. OAuth integration (Google/GitHub login)
2. Multi-subject selection
3. Learning progress tracking
4. Quiz generation based on selections
5. Collaborative features
6. Admin panel for content management
