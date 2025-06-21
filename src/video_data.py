from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass
class VideoData:
    """
    A data class to store video processing related information.
    
    Attributes:
        video_path (Path): Path to the input video file
        audio_path (Path): Path to the extracted audio file
        audio_text (str): Transcribed text from the audio
        ocr_text (str): Text extracted from video frames using OCR
        frames_dir (Path): Directory containing extracted video frames
        metadata (Dict[str, Any]): Additional metadata about the video
    """
    video_path: Path
    audio_path: Optional[Path] = None
    audio_text: Optional[str] = None
    ocr_text: Optional[str] = None
    frames_dir: Optional[Path] = None
    metadata: Dict[str, Any] = None

    def __init__(self, video_path: str | Path):
        """
        Initialize VideoData with a video file path.
        
        Args:
            video_path (str | Path): Path to the video file
            
        Raises:
            FileNotFoundError: If the video file doesn't exist
            ValueError: If the file is not a video file
        """
        # Convert string to Path if needed
        video_path = Path(video_path) if isinstance(video_path, str) else video_path
        
        # Validate video file exists
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")
            
        # Validate it's a file (not a directory)
        if not video_path.is_file():
            raise ValueError(f"Path must be a file, not a directory: {video_path}")
            
        # Validate it's a video file (basic check for common video extensions)
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        if video_path.suffix.lower() not in video_extensions:
            raise ValueError(f"File must be a video file. Supported extensions: {video_extensions}")
        
        # Initialize the dataclass
        self.video_path = video_path
        self.audio_path = None
        self.audio_text = None
        self.ocr_text = None
        self.frames_dir = None
        self.metadata = {}

    def process_video(self, processor: Optional[VideoProcessor] = None, save_audio: bool = False) -> None:
        """
        Process the video using VideoProcessor to populate all fields.
        
        Args:
            processor (VideoProcessor, optional): VideoProcessor instance. If None, creates a new one.
            save_audio (bool): If True, saves the audio file to a permanent location before processing.
        """
        if processor is None:
            processor = VideoProcessor()
            
        # If save_audio is True, create a permanent audio file path
        if save_audio:
            audio_dir = self.video_path.parent / "audio"
            audio_dir.mkdir(exist_ok=True)
            permanent_audio_path = audio_dir / f"{self.video_path.stem}.mp3"
            # Process video with the permanent audio path
            results = processor.process_video(str(self.video_path), str(permanent_audio_path))
            self.audio_path = permanent_audio_path
        else:
            # Process video with temporary audio file
            results = processor.process_video(str(self.video_path))
            # Don't store the audio path since it will be deleted
            self.audio_path = None
        
        # Update the data fields with results
        self.audio_text = results["transcript"]
        self.ocr_text = "\n".join(results["ocr_texts"])  # Join OCR texts with newlines
        self.frames_dir = Path(results["frames_path"])
        
        # Update metadata with processing information
        self.metadata.update({
            "processed": True,
            "ocr_text_count": len(results["ocr_texts"]),
            "frames_directory": str(self.frames_dir),
            "audio_saved": save_audio
        })

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.metadata is None:
            self.metadata = {}
        
        # Convert string paths to Path objects if needed
        if isinstance(self.video_path, str):
            self.video_path = Path(self.video_path)
        if isinstance(self.audio_path, str):
            self.audio_path = Path(self.audio_path)
        if isinstance(self.frames_dir, str):
            self.frames_dir = Path(self.frames_dir)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the VideoData object to a dictionary."""
        return {
            'video_path': str(self.video_path),
            'audio_path': str(self.audio_path) if self.audio_path else None,
            'audio_text': self.audio_text,
            'ocr_text': self.ocr_text,
            'frames_dir': str(self.frames_dir) if self.frames_dir else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoData':
        """Create a VideoData object from a dictionary."""
        return cls(
            video_path=data['video_path'],
            audio_path=data.get('audio_path'),
            audio_text=data.get('audio_text'),
            ocr_text=data.get('ocr_text'),
            frames_dir=data.get('frames_dir'),
            metadata=data.get('metadata', {})
        ) 