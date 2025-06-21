import unittest
import os
import tempfile
from main.backend.VideoProcessor import VideoProcessor

class TestVideoProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.video_processor = VideoProcessor()
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp()
        
        # Path to a sample video file for testing
        # Note: You'll need to provide a sample video file for testing
        self.sample_video_path = "path/to/your/sample/video.mp4"
        
    def test_audio_extraction(self):
        """Test audio extraction from video."""
        # Test audio extraction
        output_audio_path = os.path.join(self.test_output_dir, "test_audio.mp3")
        
        try:
            extracted_audio_path = self.video_processor.extract_audio(
                self.sample_video_path,
                output_audio_path
            )
            
            # Verify the audio file was created
            self.assertTrue(os.path.exists(extracted_audio_path))
            self.assertTrue(extracted_audio_path.endswith('.mp3'))
            
            # Verify the file is not empty
            self.assertGreater(os.path.getsize(extracted_audio_path), 0)
            
        finally:
            # Cleanup
            if os.path.exists(extracted_audio_path):
                os.remove(extracted_audio_path)
    
    def test_ocr_functionality(self):
        """Test OCR functionality on a sample image."""
        # Create a sample image with text for testing
        # Note: You'll need to provide a sample image with text for testing
        sample_image_path = "path/to/your/sample/image.jpg"
        
        try:
            # Test OCR on a single image
            ocr_result = self.video_processor.ocr_image(sample_image_path)
            
            # Verify OCR result is a string
            self.assertIsInstance(ocr_result, str)
            
            # Test OCR on frames
            frames_folder = self.video_processor.sample_frames(
                self.sample_video_path,
                frame_rate=1,
                output_folder=os.path.join(self.test_output_dir, "frames")
            )
            
            ocr_texts = self.video_processor.run_ocr_on_frames_gc(frames_folder)
            
            # Verify OCR results
            self.assertIsInstance(ocr_texts, list)
            
        finally:
            # Cleanup
            if os.path.exists(frames_folder):
                for file in os.listdir(frames_folder):
                    os.remove(os.path.join(frames_folder, file))
                os.rmdir(frames_folder)
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove the temporary directory and its contents
        if os.path.exists(self.test_output_dir):
            for file in os.listdir(self.test_output_dir):
                os.remove(os.path.join(self.test_output_dir, file))
            os.rmdir(self.test_output_dir)

if __name__ == '__main__':
    unittest.main() 