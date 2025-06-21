import os
import requests
import tempfile
import uuid
from urllib.parse import urlparse
from pathlib import Path
import subprocess
import shutil
from dotenv import load_dotenv

load_dotenv()
class VideoDownloader:
    def __init__(self, temp_dir=None):
        """
        Simple video downloader - downloads and returns path to video file
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Supported formats by VideoProcessor
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv']
    
    def download_video(self, url, max_size_mb=100):
        """
        Download video from URL - only convert if format is unsupported
        
        Args:
            url: URL of the video
            max_size_mb: Maximum file size in MB to download
            
        Returns:
            str: Path to downloaded video file
        """
        try:
            file_id = str(uuid.uuid4())
            
            # Get file extension from URL
            parsed_url = urlparse(url)
            original_ext = Path(parsed_url.path).suffix.lower()
            
            # If no extension, assume mp4
            if not original_ext:
                original_ext = '.mp4'
            
            temp_file = os.path.join(self.temp_dir, f"video_{file_id}{original_ext}")
            
            print(f"Downloading video from: {url}")
            
            # Stream download to check size
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Check content length if available
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    raise Exception(f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)")
            
            # Download the file
            downloaded_size = 0
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Check size during download
                        size_mb = downloaded_size / (1024 * 1024)
                        if size_mb > max_size_mb:
                            f.close()
                            os.remove(temp_file)
                            raise Exception(f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)")
            
            print(f"Downloaded {downloaded_size / (1024 * 1024):.1f}MB")
            
            # Check if format is supported
            if original_ext in self.supported_formats:
                print(f"Format {original_ext} is supported")
                return temp_file
            else:
                print(f"Format {original_ext} not supported - converting to MP4")
                return self._convert_to_mp4(temp_file)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download video: {str(e)}")
        except Exception as e:
            # Clean up any partial files
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
    
    def download_social_media_video(self, url):
        """
        Download from social media platforms or direct URLs
        """
        if self._is_direct_video_url(url):
            return self.download_video(url)
        else:
            return self._download_with_ytdlp(url)
    
    def _is_direct_video_url(self, url):
        """Check if URL points directly to a video file"""
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv']
        parsed_url = urlparse(url)
        return any(parsed_url.path.lower().endswith(ext) for ext in video_extensions)
    
    def _download_with_ytdlp(self, url):
        """
        Download using yt-dlp for social media platforms
        """
        try:
            import yt_dlp
            
            file_id = str(uuid.uuid4())
            output_template = os.path.join(self.temp_dir, f"social_video_{file_id}.%(ext)s")
            
            # Prefer supported formats
            format_selector = 'best[ext=mp4]/best[ext=mov]/best[ext=avi]/best[ext=mkv]/best'
            
            ydl_opts = {
                'outtmpl': output_template,
                'format': format_selector,
                'max_filesize': 100 * 1024 * 1024,  # 100MB limit
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Check if the downloaded format is supported
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.supported_formats:
                    print(f"Downloaded in supported format: {file_ext}")
                    return filename
                else:
                    print(f"Downloaded format {file_ext} not supported - converting...")
                    return self._convert_to_mp4(filename)
                
        except ImportError:
            raise Exception("yt-dlp not installed. Install with: pip install yt-dlp")
        except Exception as e:
            raise Exception(f"Failed to download from social media: {str(e)}")
    
    def _convert_to_mp4(self, input_path):
        """
        Convert video to MP4 format using ffmpeg
        """
        try:
            output_path = input_path.rsplit('.', 1)[0] + '.mp4'
            
            if not self._check_ffmpeg():
                raise Exception("ffmpeg not found. Please install ffmpeg to convert video formats.")
            
            print(f"Converting to MP4...")
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg conversion failed: {result.stderr}")
            
            # Remove original file
            os.remove(input_path)
            
            print("Video converted successfully")
            return output_path
            
        except Exception as e:
            # Clean up files on error
            for file_path in [input_path, output_path]:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
            raise e
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available"""
        return shutil.which('ffmpeg') is not None
    
    def cleanup_file(self, file_path):
        """Clean up downloaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up file: {file_path}")
        except Exception as e:
            print(f"Warning: Could not clean up file {file_path}: {e}")


# Simple function to download video and pass to your existing processor
def download_video(url):
    """
    Download video from URL and process with your existing VideoProcessor
    """
    
    
    downloader = VideoDownloader(temp_dir="/Users/riddhib/Documents/ReelAI/src/resources/Travel/Reels")
    temp_video_path = None
    

    # Step 1: Download the video
    print("Step 1: Downloading video...")
    temp_video_path = downloader.download_social_media_video(url)
    print(f"Video downloaded to: {temp_video_path}")
    
    
    return temp_video_path
    
        
    # finally:
    #     # Step 3: Clean up downloaded file
    #     if temp_video_path:
    #         downloader.cleanup_file(temp_video_path)