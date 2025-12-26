# -*- coding: utf-8 -*-
"""Simple test for AI analysis system."""

import os
import sys
import json
from datetime import datetime

def test_basic_setup():
    """Test basic system setup."""
    print("Testing basic setup...")
    
    # Check .env file
    if os.path.exists(".env"):
        print("✓ .env file exists")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and len(api_key) > 10:
            print("✓ API key is configured")
            print(f"  Key preview: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("✗ API key not properly configured")
            return False
    else:
        print("✗ .env file missing")
        return False
    
    # Check data files
    data_files = [
        "docs/data/stock_three_inst_latest.json",
        "docs/data/broker_ranking.json"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
    
    return True

def test_ai_modules():
    """Test AI module imports."""
    print("\nTesting AI module imports...")
    
    modules_to_test = [
        "ai_analysis.base",
        "ai_analysis.trend_analysis", 
        "ai_analysis.broker_analysis",
        "ai_analysis.sentiment_analysis",
        "ai_analysis.recommendations",
        "ai_analysis.anomaly_detection"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            return False
    
    return True

def test_ai_functionality():
    """Test basic AI functionality."""
    print("\nTesting AI functionality...")
    
    try:
        from ai_analysis.base import AIAnalysisBase
        base = AIAnalysisBase()
        
        if base.is_enabled():
            print("✓ AI analysis is enabled")
        else:
            print("✗ AI analysis is disabled")
            return False
            
        # Test simple OpenAI call
        messages = [{"role": "user", "content": "Hello, respond with just 'OK'"}]
        response = base._call_openai(messages, "You are a helpful assistant.")
        
        if response:
            print(f"✓ OpenAI API working: {response[:50]}...")
            return True
        else:
            print("✗ OpenAI API call failed")
            return False
            
    except Exception as e:
        print(f"✗ AI functionality test failed: {e}")
        return False

def run_sample_analysis():
    """Run a sample analysis."""
    print("\nRunning sample analysis...")
    
    try:
        from ai_analysis_runner import AIAnalysisOrchestrator
        orchestrator = AIAnalysisOrchestrator()
        
        # Run sentiment analysis only
        results = orchestrator.run_sentiment_only()
        
        if results and "results" in results:
            print("✓ Sample analysis completed")
            
            # Check if analysis files were created
            output_dir = "docs/data/ai_analysis"
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"  Generated {len(files)} output files")
                for file in files[:3]:  # Show first 3 files
                    print(f"    - {file}")
            
            return True
        else:
            print("✗ Sample analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Sample analysis error: {e}")
        return False

def main():
    """Run all tests."""
    print("AI Analysis System Test")
    print("=" * 40)
    
    all_passed = True
    
    # Run tests
    if not test_basic_setup():
        all_passed = False
    
    if not test_ai_modules():
        all_passed = False
    
    if not test_ai_functionality():
        all_passed = False
    
    if not run_sample_analysis():
        all_passed = False
    
    # Final result
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! System is ready.")
    else:
        print("✗ Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)