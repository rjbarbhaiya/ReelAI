#!/usr/bin/env python3
"""
Test setup script to add sample data for testing the dashboard functionality
"""

from app import app, db
from models import User, Trip, Reel
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_sample_data():
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Check if test user already exists
        test_user = User.query.filter_by(username='testuser').first()
        if test_user:
            print("Test user already exists, skipping creation")
            return test_user
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Create sample trips
        trip1 = Trip(
            user_id=test_user.id,
            name='Summer Vacation 2023',
            description='Amazing trip to Europe',
            created_at=datetime(2023, 6, 15)
        )
        
        trip2 = Trip(
            user_id=test_user.id,
            name='Weekend Getaway',
            description='Quick trip to the mountains',
            created_at=datetime(2023, 8, 20)
        )
        
        db.session.add(trip1)
        db.session.add(trip2)
        db.session.commit()
        
        # Create sample reels
        reel1 = Reel(
            user_id=test_user.id,
            url='https://example.com/video1.mp4',
            title='Paris Adventures',
            caption='Exploring the beautiful city of Paris',
            status='processed'
        )
        
        reel2 = Reel(
            user_id=test_user.id,
            url='https://example.com/video2.mp4',
            title='Mountain Hiking',
            caption='Hiking in the beautiful mountains',
            status='processed'
        )
        
        db.session.add(reel1)
        db.session.add(reel2)
        db.session.commit()
        
        # Associate reels with trips
        trip1.reels.append(reel1)
        trip2.reels.append(reel2)
        db.session.commit()
        
        print(f"Created test user: {test_user.username}")
        print(f"Created {len([trip1, trip2])} trips")
        print(f"Created {len([reel1, reel2])} reels")
        print("Sample data created successfully!")
        
        return test_user

if __name__ == "__main__":
    create_sample_data() 