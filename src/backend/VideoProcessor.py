import os
import tempfile
import ffmpeg
import whisper
import cv2
import re
from google.cloud import vision
import io
import os
import base64
from dotenv import load_dotenv
load_dotenv()

class VideoProcessor:
    def __init__(self, model_size="tiny"):
        """
        Initialize the video processor.

        Args:
            model_size (str): Whisper model size ('tiny', 'small', 'medium', 'large').
        """
        self.whisper_model = whisper.load_model(model_size)
        # self.ocr_reader = easyocr.Reader(['en'])

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.client = vision.ImageAnnotatorClient()


    def validate_video_path(self, video_path):
        """
        Validate if the file exists and is an mp4 or video file.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file '{video_path}' not found.")
        if not video_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            raise ValueError(f"Unsupported video format for file '{video_path}'. Please provide a valid video file.")

    def extract_audio(self, video_path, output_audio_path=None):
        """
        Extract audio from a video file (e.g., mp4).
        """
        if output_audio_path is None:
            # Get the directory and filename from video_path
            video_dir = os.path.dirname(video_path)
            print(video_dir)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            # Create output path in same directory with .mp3 extension
            output_audio_path = os.path.join(video_dir, "../Audio" ,f"{video_name}.MP3")
        
        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_audio_path, acodec='mp3', vn=None)  # vn disables video
                .run(overwrite_output=True, quiet=True)
            )
            return output_audio_path
        except ffmpeg.Error as e:
            print(f"An error occurred: {e.stderr.decode()}")
            print("STDOUT:", e.stdout.decode() if e.stdout else "No stdout")
            print("STDERR:", e.stderr.decode() if e.stderr else "No stderr")
            raise

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file to text using Whisper.
        """
        result = self.whisper_model.transcribe(audio_path)
        return result["text"]

    def sample_frames(self, video_path, frame_rate=1, output_folder=None):
        """
        Sample frames from video every 'frame_rate' seconds and save them to a folder.

        Args:
            video_path (str): Path to the video file
            frame_rate (int): Sample a frame every 'frame_rate' seconds
            output_folder (str): Path to save frames. If None, creates a temp directory

        Returns:
            str: Path to the folder containing saved frames
        """
        # Create output folder if not provided
        if output_folder is None:
            # Get the directory and filename from video_path
            video_dir = os.path.dirname(video_path)
            print(video_dir)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            # Create output path in same directory with .mp3 extension
            output_folder = os.path.join(video_dir, "../ImageFrames" ,video_name)
        
        # Ensure the output directory exists
        os.makedirs(output_folder, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = 0
            saved_count = 0
            
            while True:
                frame_id = cap.get(cv2.CAP_PROP_POS_FRAMES)
                success, frame = cap.read()
                if not success:
                    break
                    
                if frame_id % (fps * frame_rate) < 1:
                    frame_path = os.path.join(output_folder, f"frame_{saved_count:04d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    saved_count += 1
                
                frame_count += 1
                
            print(f"[INFO] Saved {saved_count} frames to {output_folder}")
            return output_folder

        finally:
            cap.release()
    
    def normalize_text(self, text):
        """
        Normalize text for deduplication:
        - Lowercase
        - Remove punctuation
        - Collapse multiple spaces
        """
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)  # remove non-alphanumeric except spaces
        text = re.sub(r'\s+', ' ', text).strip()  # collapse multiple spaces
        return text

    def run_ocr_on_frames(self, frames_folder):
        """
        Run OCR on each frame image in the specified folder and collect unique normalized texts.

        Args:
            frames_folder (str): Path to the folder containing frame images

        Returns:
            List of unique detected texts (preserving original casing for display).
        """
        seen_texts = set()
        unique_ocr_texts = []

        # Get all jpg files from the folder
        frame_files = sorted([
            os.path.join(frames_folder, f) 
            for f in os.listdir(frames_folder) 
            if f.endswith('.jpg')
        ])

        for frame_path in frame_files:
            # Read the image file
            frame = cv2.imread(frame_path)
            if frame is None:
                print(f"Warning: Could not read frame {frame_path}")
                continue

            result = self.ocr_reader.readtext(frame)
            frame_texts = [text[1] for text in result]  # extract just the text parts

            for text in frame_texts:
                clean_text = text.strip()
                normalized = self.normalize_text(clean_text)

                if normalized and normalized not in seen_texts:
                    seen_texts.add(normalized)
                    unique_ocr_texts.append(clean_text)  # Save the original text for the user

        return unique_ocr_texts
    
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
        
    def ocr_image(self, image_path):
        """Perform OCR on an image file."""
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        
        texts = response.text_annotations
        if texts:
            return texts[0].description.strip()
        return ""

    def clean_ocr_texts(self, ocr_texts):
        """
        Cleans OCR results by removing duplicates, nonsensical text, and standardizing format.
        
        Args:
            ocr_texts (list of str): List of raw OCR strings.
            
        Returns:
            list of str: Cleaned OCR strings.
        """
        cleaned_texts = []
        seen_texts = set()

        # Pattern to match various TikTok variations
        tiktok_pattern = r'\s*(?:Tik\s*Tok|TikTok|TikTol|kTok|Tik\s*Tok)\s*'

        for text in ocr_texts:
            # Split into lines to clean line-by-line
            lines = text.splitlines()
            new_lines = []

            for line in lines:
                # Normalize spacing and remove leading/trailing whitespace
                line = line.strip()

                # Skip if line is too short or contains only non-alphanumeric characters
                if len(line) < 3 or not any(c.isalnum() for c in line):
                    continue

                # Remove TikTok variations from start and end of line
                line = re.sub(f'^{tiktok_pattern}|{tiktok_pattern}$', '', line, flags=re.IGNORECASE)
                
                # Remove handles like "@connoisseurofluxury" or "@ connoisseurofluxury"
                line = re.sub(r"@\s*\w+", "", line)
                
                # Remove common OCR artifacts and nonsensical text
                line = re.sub(r'\s*(J|NNS|VI|VIT|FINN|UTORIA|Pintu K|Exit Gate|an|كل|Ժ)\s*$', '', line, flags=re.IGNORECASE)
                
                
                # Remove non-English characters
                line = re.sub(r'[^\x00-\x7F]+', '', line)
                
                # Standardize spacing around currency symbols and numbers
                line = re.sub(r'(\d+)\s*([£$€])\s*(\d+)', r'\1\2\3', line)
                line = re.sub(r'([£$€])\s*(\d+)', r'\1\2', line)
                
                # Remove multiple spaces
                line = re.sub(r'\s+', ' ', line)
                
                # Remove dangling characters and re-strip
                line = re.sub(r'^\W+|\W+$', '', line).strip()

                # Skip empty lines
                if line:
                    new_lines.append(line)

            # Recombine cleaned lines
            cleaned_text = ' '.join(new_lines)
            
            # Normalize the text for deduplication
            normalized = self.normalize_text(cleaned_text)
            
            # Only add if we haven't seen this text before
            if normalized and normalized not in seen_texts:
                seen_texts.add(normalized)
                cleaned_texts.append(cleaned_text)

        return cleaned_texts

    def run_ocr_on_frames_gc(self, frames_folder):
        """
        Run OCR on each frame image in the specified folder and collect unique normalized texts.

        Args:
            frames_folder (str): Path to the folder containing frame images

        Returns:
            List of unique detected texts (preserving original casing for display).
        """
        seen_texts = set()
        unique_ocr_texts = []

        # Get all jpg files from the folder
        frame_files = sorted([
            os.path.join(frames_folder, f) 
            for f in os.listdir(frames_folder) 
            if f.endswith('.jpg')
        ])

        for frame_path in frame_files:
            with io.open(frame_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            annotations = response.text_annotations

            if annotations:
                # The first result is the full detected text
                full_text = annotations[0].description.strip()
                
                # Clean the text before checking for duplicates
                cleaned_text = self.clean_ocr_texts([full_text])[0] if self.clean_ocr_texts([full_text]) else ""
                if not cleaned_text:
                    continue
                    
                normalized = self.normalize_text(cleaned_text)

                if normalized and normalized not in seen_texts:
                    seen_texts.add(normalized)
                    unique_ocr_texts.append(cleaned_text)

        return unique_ocr_texts

    def process_video(self, video_path, output_path = ""):
        """
        Full pipeline: process video and return extracted text data.

        Returns:
            Dictionary with 'transcript' and 'ocr_texts'
        """
        self.validate_video_path(video_path)

        # if output_path == "":
        #     # Get the directory and filename from video_path
        #     video_dir = os.path.dirname(video_path)
        #     video_name = os.path.splitext(os.path.basename(video_path))[0]
        #     # Create output path in same directory with .mp3 extension
        #     output_path = os.path.join(video_dir, f"{video_name}.MP3")

        print("[INFO] Extracting audio...")
        audio_path = self.extract_audio(video_path)

        print("[INFO] Transcribing audio...")
        transcript = self.transcribe_audio(audio_path)

        print("[INFO] Sampling frames...")
        frames_path = self.sample_frames(video_path)

        print("[INFO] Running OCR on frames...")
        ocr_texts = self.run_ocr_on_frames_gc(frames_path)

        # Cleanup temporary audio file
        # os.remove(audio_path)

        return {
            "video_path": video_path,
            "audio_path": audio_path,
            "transcript": transcript,
            "ocr_texts": ocr_texts,
            "frames_path": frames_path  # Optional: return the frames path if needed
        }
