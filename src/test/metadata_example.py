#!/usr/bin/env python3
"""
Example script demonstrating metadata extraction from video URLs
"""

from VideoDownloader import VideoDownloader, download_video

def example_metadata_extraction():
    """Example of extracting metadata from various video platforms"""
    
    # Test URLs (replace with actual URLs)
    test_urls = [
        "https://www.instagram.com/p/C9TtK2uxHol/",  # Instagram
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # YouTube
        "https://www.tiktok.com/@username/video/1234567890",  # TikTok
    ]
    
    downloader = VideoDownloader()
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print(f"{'='*60}")
        
        try:
            # Method 1: Extract metadata only (without downloading)
            print("\n1. Extracting metadata only...")
            metadata = downloader.extract_metadata(url)
            if metadata:
                print("Metadata extracted:")
                for key, value in metadata.to_dict().items():
                    print(f"  {key}: {value}")
            else:
                print("No metadata available")
            
            # Method 2: Download video with metadata
            print("\n2. Downloading video with metadata...")
            video_path, metadata = downloader.download_video_with_metadata(url)
            print(f"Video downloaded to: {video_path}")
            if metadata:
                print("Metadata:")
                for key, value in metadata.to_dict().items():
                    print(f"  {key}: {value}")
            
            # Clean up
            downloader.cleanup_file(video_path)
            
        except Exception as e:
            print(f"Error processing {url}: {e}")

def example_using_function():
    """Example using the simplified download_video function"""
    
    url = "https://www.instagram.com/p/C9TtK2uxHol/"
    
    print(f"\n{'='*60}")
    print(f"Using download_video function with metadata")
    print(f"{'='*60}")
    
    try:
        # Download with metadata
        video_path, metadata = download_video(url, include_metadata=True)
        print(f"Video path: {video_path}")
        if metadata:
            print("Metadata:")
            for key, value in metadata.to_dict().items():
                print(f"  {key}: {value}")
        
        # Clean up
        downloader = VideoDownloader()
        downloader.cleanup_file(video_path)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Video Metadata Extraction Examples")
    print("=" * 60)
    
    # Run examples
    example_metadata_extraction()
    example_using_function() 