from flask import Flask, render_template, jsonify, request, session
import json
import os
from dotenv import load_dotenv
from backend.MainProcess import process_video
from VideoDownloader import download_video  

# Load environment variables from .env file
load_dotenv()

app = Flask(
    __name__, 
    static_folder='frontend/static',
    template_folder='frontend/templates')

# Add a secret key for sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY") # Use environment variable

# Store processed destinations temporarily
processed_destinations = {}

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/map")
def map_page():
    google_maps_api_key = os.getenv('GOOGLE_API')
    return render_template("map.html", google_maps_api_key=google_maps_api_key)

@app.route("/process", methods=["POST"])
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
        
        # Download and process the video
        result = download_video(video_url)
        #TODO: delete the downloaded video
        # Extract what you need from the result for your destinations
        # You'll need to implement this part based on how you convert
        # transcript + OCR texts to destination data
        destinations = process_video(result)
        
        if not destinations:
            return jsonify({"error": "No destinations found in the video"}), 400
        
        # Store the results temporarily
        processed_destinations[session_id] = destinations
        
        print(f"Successfully processed video. Found {len(destinations)} destinations.")
        return jsonify({"success": True, "destinations_count": len(destinations)})
        
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return jsonify({"error": f"Failed to process video: {str(e)}"}), 500

@app.route("/destinations")
def get_destinations():
    try:
        session_id = session.get('session_id')
        if session_id and session_id in processed_destinations:
            destinations = processed_destinations[session_id]
            return jsonify(destinations)
        else:
            # Fallback to your original implementation if no session data
            print("No session data found, using fallback local file")
            destinations = process_video("/Users/riddhib/Documents/ReelAI/src/resources/Travel/Reels/3.MP4")
            return jsonify(destinations)
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