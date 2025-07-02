# VideoDownloader Test Suite

This directory contains comprehensive tests for the `VideoDownloader` class and its metadata extraction functionality.

## Test Structure

### Test Classes

1. **TestVideoMetadata** - Tests for the `VideoMetadata` class
   - Object creation with all fields
   - Object creation with partial fields
   - Dictionary conversion

2. **TestVideoDownloader** - Tests for the `VideoDownloader` class
   - Initialization and configuration
   - Direct video URL detection
   - FFmpeg availability checking
   - File cleanup functionality
   - Metadata extraction (with mocked yt-dlp)
   - Error handling

3. **TestDownloadVideoFunction** - Tests for the `download_video` function
   - Download with and without metadata
   - Error handling

4. **TestIntegration** - Integration tests with real URLs
   - Real Instagram metadata extraction
   - Real YouTube metadata extraction
   - **Note**: These tests are skipped by default

## Running Tests

### Quick Start

Run all unit tests (recommended for development):
```bash
cd src/test
python run_tests.py
```

### Test Options

Run specific types of tests:
```bash
# Unit tests only (default)
python run_tests.py --type unit

# Integration tests only (requires internet connection)
python run_tests.py --type integration

# All tests
python run_tests.py --type all
```

Run specific test categories:
```bash
# Test only metadata functionality
python run_tests.py --test metadata

# Test only downloader functionality
python run_tests.py --test downloader

# Test only function wrapper
python run_tests.py --test function

# Test only integration (real URLs)
python run_tests.py --test integration
```

### Direct Test Execution

You can also run tests directly:
```bash
# Run all tests
python test_video_downloader.py

# Run with more verbose output
python -m unittest test_video_downloader -v
```

## Test Coverage

### Unit Tests (Mocked)
- ✅ VideoMetadata object creation and methods
- ✅ VideoDownloader initialization
- ✅ Direct video URL detection
- ✅ FFmpeg availability checking
- ✅ File cleanup operations
- ✅ Metadata extraction with mocked yt-dlp responses
- ✅ Error handling for missing dependencies
- ✅ Error handling for extraction failures
- ✅ Download function wrapper behavior

### Integration Tests (Real URLs)
- ⚠️ Real Instagram metadata extraction (skipped by default)
- ⚠️ Real YouTube metadata extraction (skipped by default)

## Prerequisites

### Required Dependencies
- `unittest` (built-in)
- `unittest.mock` (built-in)
- `tempfile` (built-in)
- `os` (built-in)

### Optional Dependencies (for integration tests)
- `yt-dlp` - For real metadata extraction
- Internet connection - For accessing real video URLs

## Test Data

### Mock Data
The unit tests use mocked responses that simulate real yt-dlp output:
```python
mock_info = {
    'title': 'Test Video Title',
    'description': 'Test video description',
    'thumbnail': 'https://example.com/thumb.jpg',
    'upload_date': '20240101',
    'duration': 120.5,
    'uploader': 'Test Channel'
}
```

### Real URLs (for integration tests)
- Instagram: `https://www.instagram.com/p/C9TtK2uxHol/`
- YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

## Continuous Integration

These tests are designed to run in CI/CD environments:
- Unit tests run quickly and don't require external dependencies
- Integration tests are optional and can be skipped in CI
- Tests clean up after themselves (temporary files, etc.)
- Exit codes are properly set for CI systems

## Adding New Tests

### For New Features
1. Add test methods to the appropriate test class
2. Use descriptive test method names starting with `test_`
3. Include both positive and negative test cases
4. Mock external dependencies when possible

### For Bug Fixes
1. Add a test that reproduces the bug
2. Verify the test fails before fixing
3. Implement the fix
4. Verify the test passes

### Test Naming Convention
- `test_<method_name>_<scenario>` for method tests
- `test_<feature>_<condition>` for feature tests
- `test_<error_type>_handling` for error handling tests

## Troubleshooting

### Common Issues

**Import Error**: Make sure you're running tests from the `src/test` directory or that the parent directory is in your Python path.

**Mock Issues**: If mocks aren't working, check that you're patching the correct import path. The path should match how the module is imported in the code being tested.

**Integration Test Failures**: Integration tests may fail due to:
- Network connectivity issues
- Changes in platform APIs
- Rate limiting
- Authentication requirements

### Debug Mode
Run tests with increased verbosity:
```bash
python -m unittest test_video_downloader -v -f
```

The `-f` flag stops on first failure, and `-v` provides detailed output. 