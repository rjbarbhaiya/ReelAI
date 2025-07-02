import os
import backend.VideoProcessor as vp
import backend.GenAIProcessor as gip
import backend.MapDestinationExporter as mde
from VideoDownloader import download_video
from dotenv import load_dotenv
from models import Reel,db,Destination
from datetime import datetime
import backend.auth_service as auth

load_dotenv()

def process_video(video_url, user_id):
    """
    Process a video URL and extract destinations
    
    Args:
        video_url (str): URL of the video to process
        user_id (int): ID of the user processing the video
        
    Returns:
        list: List of location objects with destination information
    """
    print(user_id)
    try:
        key = os.getenv("GOOGLE_API")
        if not key:
            raise ValueError("GOOGLE_API environment variable not found. Please check your .env file.")
        
        openai_key = os.getenv("OPEN_AI")
        if not openai_key:
            raise ValueError("OPEN_AI environment variable not found. Please check your .env file.")
        
        # Download video and extract metadata
        video_path, metadata = download_video(video_url, True)
        print(f"Downloaded video: {video_path}")
        print(f"Extracted metadata: {metadata.to_dict() if metadata else 'None'}")

        # Process video to extract transcript and OCR text
        videoProcessor = vp.VideoProcessor()
        outputTravel = videoProcessor.process_video(video_path)
        print(f"Video processing completed. Transcript length: {len(outputTravel['transcript'])}")

        # Save reel to database
        reelID = writeReelToDB(video_url, user_id, metadata, outputTravel['transcript'])
        
        # Process OCR text to extract destinations
        genAIProcessor = gip.GenAIProcessor(openai_key)
        print(f"Processing OCR texts: {outputTravel['ocr_texts']}")
        ocr_destinations = genAIProcessor.process_ocr_text(outputTravel['ocr_texts'], reelID)
        print("OCR Destinations: " + str(ocr_destinations))
        ocr_destinationIDs = writeDestinationsToDB(ocr_destinations, reelID)
        
        #Process transcript to extract destinations (commented out for now)
        transcript_destinations = genAIProcessor.process_transcript(outputTravel['transcript'], reelID)
        print("Transcript Destinations: " + str(transcript_destinations))
        transcript_destinationIDs = writeDestinationsToDB(transcript_destinations, reelID)

        # Export destinations to map
        mapDestinationExporter = mde.MapDestinationExporter(key)
        #mapDestinationExporter = mde.MapDestinationExporter(key,transcript_destinationIDs)

        print(f"Exporting {len(ocr_destinations)} destinations to map")
        mapDestinationExporter.run(ocr_destinations,ocr_destinationIDs)
        
        return mapDestinationExporter.locations
        
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise

def writeDestinationsToDB(destinations, reelID):
    destinationIDs = []
    for index,dest in enumerate(destinations):
        # Check for existing destination with the same reelID and (case-insensitive) name
        existing = Destination.query.filter(
            Destination.reel_id == reelID,
            db.func.lower(Destination.name) == dest.name.strip().lower()
        ).first()
        if existing:
            destinations.pop(index)
            print(f"Destination '{dest.name}' already exists for reel {reelID}, skipping.")
            continue

        db.session.add(dest)
        db.session.commit()
        destinationIDs.append(dest.id)
    
    if (len(destinations) != len (destinationIDs)):
        print("Somethiing wrong with writeDestinationsToDB")
    return destinationIDs


def writeReelToDB(video_url, userID, metaData, transcript):
    """
    Write reel data to database with proper error handling and data validation
    
    Args:
        video_url (str): URL of the video
        userID (int): User ID
        metaData (VideoMetadata): Metadata object from VideoDownloader
        transcript (str): Video transcript
        
    Returns:
        Reel: The created reel object
        
    Raises:
        ValueError: If required data is missing or invalid
        Exception: If database operation fails
    """
    try:
        # Check if reel already exists for this user and url
        existing_reel = Reel.query.filter_by(user_id=userID, url=video_url).first()
        if existing_reel:
            print(f"Reel already exists for user {userID} and url {video_url}, returning existing reel ID: {existing_reel.id}")
            return existing_reel.id
        # Validate required parameters
        if not video_url:
            raise ValueError("video_url is required")
        if not userID:
            raise ValueError("userID is required")
        if not metaData:
            raise ValueError("metaData is required")
        if not transcript:
            raise ValueError("transcript is required")
        
        # Convert upload_date string to datetime object
        upload_datetime = None
        if metaData.upload_date:
            try:
                # Parse YYYYMMDD format to datetime
                upload_datetime = datetime.strptime(metaData.upload_date, '%Y%m%d')
            except ValueError:
                # If parsing fails, use current datetime
                upload_datetime = datetime.utcnow()
                print(f"Warning: Could not parse upload_date '{metaData.upload_date}', using current time")
        else:
            upload_datetime = datetime.utcnow()
        
        # Convert duration to milliseconds (handle None case)
        duration_ms = None
        if metaData.duration is not None:
            duration_ms = int(metaData.duration * 1000)

        # Create new reel object
        newReel = Reel(
            user_id=userID,
            url=video_url,
            title=metaData.title,
            caption=metaData.caption,
            transcript=transcript,
            uploaded_at=upload_datetime,
            status='processed',
            thumbnail_url=metaData.thumbnail_url,
            duration_ms=duration_ms
        )
        
        # Add to database session and commit
        db.session.add(newReel)
        db.session.commit()
        
        print(f"Successfully saved reel to database with ID: {newReel.id}")
        return newReel.id
        
    except Exception as e:
        # Rollback on error
        db.session.rollback()
        print(f"Error saving reel to database: {str(e)}")
        raise

