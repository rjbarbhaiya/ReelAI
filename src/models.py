from db import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reels = db.relationship('Reel', backref='user', lazy=True)
    trips = db.relationship('Trip', backref='user', lazy=True)

class Reel(db.Model):
    __tablename__ = 'reels'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    url = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.Text)
    caption = db.Column(db.Text)
    transcript = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='processed')
    thumbnail_url = db.Column(db.Text)
    duration_ms = db.Column(db.Integer)

    destinations = db.relationship('Destination', backref='reel', lazy=True)

class Destination(db.Model):
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    reel_id = db.Column(db.Integer, db.ForeignKey('reels.id'), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    confidence = db.Column(db.Numeric(5, 4), default=0.0) 

    location = db.relationship('Location', backref='destination', uselist=False)

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    place_id = db.Column(db.Text)
    address = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'destination_id': self.destination_id,
            'lat': self.lat,
            'lng': self.lng,
            'place_id': self.place_id,
            'address': self.address
        }

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reels = db.relationship('Reel', secondary='trip_reels', backref='trips')
    destinations = db.relationship('Destination', backref='trip', lazy=True)

class TripReel(db.Model):
    __tablename__ = 'trip_reels'
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), primary_key=True)
    reel_id = db.Column(db.Integer, db.ForeignKey('reels.id'), primary_key=True)
