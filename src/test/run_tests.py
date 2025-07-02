#!/usr/bin/env python3
"""
Test runner for VideoDownloader tests
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import VideoDownloader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_video_downloader import (
    TestVideoMetadata,
    TestVideoDownloader,
    TestDownloadVideoFunction,
    TestIntegration
)


def run_unit_tests():
    """Run all unit tests (excluding integration tests)"""
    print("Running Unit Tests...")
    print("=" * 50)
    
    # Create test suite for unit tests
    unit_test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add unit test classes using the newer method
    unit_test_suite.addTest(loader.loadTestsFromTestCase(TestVideoMetadata))
    unit_test_suite.addTest(loader.loadTestsFromTestCase(TestVideoDownloader))
    unit_test_suite.addTest(loader.loadTestsFromTestCase(TestDownloadVideoFunction))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unit_test_suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests with real URLs"""
    print("Running Integration Tests...")
    print("=" * 50)
    
    # Create test suite for integration tests
    integration_test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    integration_test_suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(integration_test_suite)
    
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests including integration tests"""
    print("Running All Tests...")
    print("=" * 50)
    
    # Create test suite for all tests
    all_test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add all test classes using the newer method
    all_test_suite.addTest(loader.loadTestsFromTestCase(TestVideoMetadata))
    all_test_suite.addTest(loader.loadTestsFromTestCase(TestVideoDownloader))
    all_test_suite.addTest(loader.loadTestsFromTestCase(TestDownloadVideoFunction))
    all_test_suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_test_suite)
    
    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test by name"""
    print(f"Running Test: {test_name}")
    print("=" * 50)
    
    # Create test suite for specific test
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Map test names to test classes
    test_classes = {
        'metadata': TestVideoMetadata,
        'downloader': TestVideoDownloader,
        'function': TestDownloadVideoFunction,
        'integration': TestIntegration
    }
    
    if test_name in test_classes:
        test_suite.addTest(loader.loadTestsFromTestCase(test_classes[test_name]))
    else:
        print(f"Unknown test: {test_name}")
        print("Available tests: metadata, downloader, function, integration")
        return False
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run VideoDownloader tests')
    parser.add_argument('--type', choices=['unit', 'integration', 'all'], 
                       default='unit', help='Type of tests to run')
    parser.add_argument('--test', help='Run specific test (metadata, downloader, function, integration)')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.type == 'unit':
        success = run_unit_tests()
    elif args.type == 'integration':
        success = run_integration_tests()
    elif args.type == 'all':
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 