from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from flask import session
import re
from sqlalchemy.orm import joinedload


class AuthService:
    """Service class to handle authentication logic"""
    
    @staticmethod
    def validate_registration_data(data):
        """Validate registration form data"""
        errors = []
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Check required fields
        if not username or not email or not password:
            errors.append("All fields are required")
            return errors
        
        # Validate username
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Please enter a valid email address")
        
        # Validate password
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        # Check password confirmation
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        return errors
    
    @staticmethod
    def check_user_exists(username, email):
        """Check if user already exists with given username or email"""
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        return existing_user is not None
    
    @staticmethod
    def create_user(username, email, password):
        """Create a new user"""
        try:
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return new_user, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def authenticate_user(username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            # Find user by username or email
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            if user and check_password_hash(user.password_hash, password):
                return user, None
            else:
                return None, "Invalid credentials"
                
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def login_user(user):
        """Log in a user by setting session data"""
        session['user_id'] = user.id
        session['username'] = user.username
    
    @staticmethod
    def logout_user():
        """Log out user by clearing session"""
        session.clear()
    
    @staticmethod
    def get_current_user():
        """Get current user from session"""
        if 'user_id' not in session:
            return None
        return User.query.get(session['user_id'])
    
    @staticmethod
    def is_authenticated():
        """Check if user is currently authenticated"""
        return 'user_id' in session 
    
    @staticmethod
    def get_user_id_by_username(username):
        user = User.query.filter_by(username=username).first()
        if user:
            return user.id
        else:
            return None 

    @staticmethod
    def get_trip_with_destinations(trip_id, user):
        """Get a trip with its destinations and their locations"""
        try:
            trip = Trip.query.options(
                joinedload(Trip.reels)
                .joinedload(Reel.destinations)
                .joinedload(Destination.location)
            ).filter_by(id=trip_id, user_id=user.id).first()
            
            if trip:
                return trip, None
            else:
                return None, "Trip not found"
        except Exception as e:
            return None, str(e) 