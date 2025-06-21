import os
import backend.VideoProcessor as vp
import backend.GenAIProcessor as gip
import backend.MapDestinationExporter as mde
from dotenv import load_dotenv

load_dotenv()

def process_video(video_path):
    key = os.getenv("GOOGLE_API")
    if not key:
        raise ValueError("GOOGLE_API environment variable not found. Please check your .env file.")
    
    openai_key = os.getenv("OPEN_AI")
    if not openai_key:
        raise ValueError("OPEN_AI environment variable not found. Please check your .env file.")
    
    videoProcessor = vp.VideoProcessor()
    outputTravel = videoProcessor.process_video(video_path)
    
    genAIProcessor = gip.GenAIProcessor(openai_key)
    
    print(outputTravel['ocr_texts'])
    ocr_destinations = genAIProcessor.process_ocr_text(outputTravel['ocr_texts'])
    print("OCR Dest: " + str(ocr_destinations))
    # transcript_destinations = genAIProcessor.process_transcript(outputTravel['transcript'])
    # print("Transcript Dest: " + str(transcript_destinations))

    # destinations = genAIProcessor.combine_modalities(transcript_destinations, ocr_destinations)
    # print(destinations)

    mapDestinationExporter = mde.MapDestinationExporter(key)
    print(mapDestinationExporter)
    mapDestinationExporter.run(ocr_destinations)
    return mapDestinationExporter.locations




