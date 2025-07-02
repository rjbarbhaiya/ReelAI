from flask import Flask, render_template, jsonify, request, session, redirect, flash, url_for
import json
import os
from dotenv import load_dotenv
from backend.MainProcess import process_video
from VideoDownloader import download_video  
from flask_migrate import Migrate
from config import Config
from models import db, Reel, Destination, Location, User, Trip
from functools import wraps
import uuid
from backend.auth_service import AuthService


# Load environment variables from .env file
load_dotenv()

app = Flask(
    __name__, 
    static_folder='frontend/static',
    template_folder='frontend/templates')

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

processed_destinations = {}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if AuthService.is_authenticated():
        return redirect(url_for('dashboard'))
    return render_template("landing.html")

@app.route("/clear-session")
def clear_session():
    AuthService.logout_user()
    return redirect(url_for('index'))

@app.route("/dashboard")
@login_required
def dashboard():
    user = AuthService.get_current_user()
    user_reels = Reel.query.filter_by(user_id=user.id).all()
    user_trips = Trip.query.filter_by(user_id=user.id).all()
    return render_template("dashboard.html", user=user, reels=user_reels, trips=user_trips)

@app.route("/api/user/trips")
@login_required
def get_user_trips():
    user = AuthService.get_current_user()
    trips = Trip.query.filter_by(user_id=user.id).all()
    
    trips_data = []
    for trip in trips:
        trip_data = {
            'id': trip.id,
            'name': trip.name,
            'description': trip.description,
            'created_at': trip.created_at.isoformat(),
            'reels_count': len(trip.reels)
        }
        trips_data.append(trip_data)
    
    return jsonify({"success": True, "trips": trips_data})

@app.route("/api/trips", methods=["POST"])
@login_required
def create_trip():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({"error": "Trip name is required"}), 400
        
        user = AuthService.get_current_user()
        new_trip = Trip(
            user_id=user.id,
            name=name,
            description=description
        )
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "trip": {
                'id': new_trip.id,
                'name': new_trip.name,
                'description': new_trip.description
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating trip: {str(e)}")
        return jsonify({"error": "Failed to create trip"}), 500

@app.route("/api/trips/<int:trip_id>/locations", methods=["POST"])
@login_required
def add_locations_to_trip(trip_id):
    try:
        data = request.get_json()
        locations = data.get('locations', [])
        
        if not locations:
            return jsonify({"error": "No locations provided"}), 400
        
        # Verify trip belongs to user
        user = AuthService.get_current_user()
        trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
        
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
        
        # Create destinations and locations
        for loc_data in locations:
            # Create destination
            destination = Destination(
                reel_id=None,  # Will be set when we have reel functionality
                name=loc_data.get('name', 'Unknown Location'),
                context=loc_data.get('context', '')
            )
            db.session.add(destination)
            db.session.flush()  # Get the ID
            
            # Create location
            location = Location(
                destination_id=destination.id,
                lat=loc_data.get('lat'),
                lng=loc_data.get('lng'),
                formatted_name=loc_data.get('formatted_name', loc_data.get('name'))
            )
            db.session.add(location)
        
        db.session.commit()
        return jsonify({"success": True, "message": f"Added {len(locations)} locations to trip"})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding locations to trip: {str(e)}")
        return jsonify({"error": "Failed to add locations to trip"}), 500

@app.route("/trip/<int:trip_id>")
@login_required
def trip_view(trip_id):
    user = AuthService.get_current_user()
    trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
    
    if not trip:
        return redirect(url_for('dashboard'))
    
    # Get all destinations for this trip
    destinations = []
    for reel in trip.reels:
        for destination in reel.destinations:
            if destination.location:
                destinations.append({
                    'id': destination.id,
                    'name': destination.name,
                    'context': destination.context,
                    'lat': destination.location.lat,
                    'lng': destination.location.lng,
                    'formatted_name': destination.location.formatted_name
                })
    
    return render_template("trip.html", trip=trip, destinations=destinations, user=user)

@app.route("/api/trips/<int:trip_id>/destinations")
@login_required
def get_trip_destinations(trip_id):
    user = AuthService.get_current_user()
    trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
    
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    
    destinations = []
    for reel in trip.reels:
        for destination in reel.destinations:
            if destination.location:
                destinations.append({
                    'id': destination.id,
                    'name': destination.name,
                    'context': destination.context,
                    'lat': destination.location.lat,
                    'lng': destination.location.lng,
                    'formatted_name': destination.location.formatted_name
                })
    
    return jsonify({"success": True, "destinations": destinations})

@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            data = request.get_json() if request.is_json else request.form
            
            # Validate registration data
            errors = AuthService.validate_registration_data(data)
            if errors:
                return jsonify({"error": errors[0]}), 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            # Check if user already exists
            if AuthService.check_user_exists(username, email):
                return jsonify({"error": "Username or email already exists"}), 400
            
            # Create new user
            new_user, error = AuthService.create_user(username, email, password)
            if error:
                return jsonify({"error": "Registration failed. Please try again."}), 500
            
            # Log the user in automatically
            AuthService.login_user(new_user)
            
            return jsonify({"success": True, "message": "Registration successful!"})
            
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({"error": "Registration failed. Please try again."}), 500
    
    return render_template("auth/register.html")

@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            data = request.get_json() if request.is_json else request.form
            username_or_email = data.get('username_or_email', '').strip()
            password = data.get('password', '')
            
            if not username_or_email or not password:
                return jsonify({"error": "Please provide username/email and password"}), 400
            
            # Authenticate user
            user, error = AuthService.authenticate_user(username_or_email, password)
            if error:
                return jsonify({"error": error}), 401
            
            # Log in user
            AuthService.login_user(user)
            return jsonify({"success": True, "message": "Login successful!"})
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({"error": "Login failed. Please try again."}), 500
    
    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    AuthService.logout_user()
    return redirect(url_for('index'))

@app.route("/profile")
@login_required
def profile():
    user = AuthService.get_current_user()
    user_reels = Reel.query.filter_by(user_id=user.id).all()
    return render_template("profile.html", user=user, reels=user_reels)

@app.route("/map")
@login_required
def map_page():
    google_maps_api_key = os.getenv('GOOGLE_API')
    return render_template("map.html", google_maps_api_key=google_maps_api_key)

def convert_destinations_to_dicts(destinations):
    """Helper function to convert destination objects to dictionaries"""
    destinations_dicts = []
    for dest in destinations:
        if hasattr(dest, 'to_dict'):
            # If the object has a to_dict method, use it
            destinations_dicts.append(dest.to_dict())
        elif isinstance(dest, dict):
            # If it's already a dictionary, keep it as is
            destinations_dicts.append(dest)
        else:
            # Manual conversion for objects without to_dict method
            dest_dict = {}
            # Add common attributes - adjust these based on your actual model structure
            for attr in ['id', 'name', 'context', 'lat', 'lng', 'formatted_name']:
                if hasattr(dest, attr):
                    dest_dict[attr] = getattr(dest, attr)
            
            # Handle location relationship if it exists
            if hasattr(dest, 'location') and dest.location:
                location = dest.location
                dest_dict.update({
                    'lat': getattr(location, 'lat', None),
                    'lng': getattr(location, 'lng', None),
                    'formatted_name': getattr(location, 'formatted_name', '')
                })
            
            destinations_dicts.append(dest_dict)
    
    return destinations_dicts

@app.route("/process", methods=["POST"])
@login_required
def process_url():
    try:
        data = request.get_json()
        video_url = data.get('url')
        
        if not video_url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Validate URL format
        if not (video_url.startswith('http://') or video_url.startswith('https://')):
            return jsonify({"error": "Invalid URL format. Please include http:// or https://"}), 400
        
        # Generate a unique session ID to store the results
        session_id = session.get('session_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        print(f"Processing video from URL: {video_url}")
        
        # Process the video and get destinations
        destinations = process_video(video_url, AuthService.get_current_user().id)
        
        if not destinations:
            return jsonify({"error": "No destinations found in the video"}), 400
        
        # CRITICAL: Convert to dictionaries before storing
        destinations_dicts = convert_destinations_to_dicts(destinations)
        
        # Store the dictionary versions instead of the model objects
        processed_destinations[session_id] = destinations_dicts
        
        print(f"Successfully processed video. Found {len(destinations_dicts)} destinations.")
        return jsonify({"success": True, "destinations_count": len(destinations_dicts)})
        
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return jsonify({"error": f"Failed to process video: {str(e)}"}), 500

@app.route("/destinations")
@login_required
def get_destinations():
    try:
        session_id = session.get('session_id')
        if session_id and session_id in processed_destinations:
            # These are already dictionaries, so we can return them directly
            destinations_dicts = processed_destinations[session_id]
        else:
            print("No session data found, using fallback local file")
            destinations = process_video("/Users/riddhib/Documents/ReelAI/src/resources/Travel/Reels/3.MP4", AuthService.get_current_user().id)
            # Convert the fallback destinations to dictionaries too
            destinations_dicts = convert_destinations_to_dicts(destinations)
        
        return jsonify(destinations_dicts)
    except Exception as e:
        print(f"Error getting destinations: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Optional: Add a route to check processing status
@app.route("/status")
def check_status():
    session_id = session.get('session_id')
    if session_id and session_id in processed_destinations:
        return jsonify({"ready": True, "destinations_count": len(processed_destinations[session_id])})
    else:
        return jsonify({"ready": False})

if __name__ == "__main__":
    app.run(debug=True)