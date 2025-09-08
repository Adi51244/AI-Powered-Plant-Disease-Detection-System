#!/usr/bin/env python3
"""
Test script for Gemini AI API integration
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import google.generativeai as genai
    print("✅ Google Generative AI library imported successfully")
except ImportError:
    print("❌ google-generativeai package not found. Install it with:")
    print("   pip install google-generativeai")
    sys.exit(1)

def load_env_vars():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        print("❌ No .env file found")
        return {}
    return env_vars

def test_gemini_api():
    """Test Gemini API functionality"""
    print("🔍 Testing Google Gemini API")
    print("=" * 50)
    
    # Load environment variables
    env_vars = load_env_vars()
    gemini_api_key = env_vars.get('GEMINI_API_KEY', '')
    
    print(f"📋 API Key: {'✅ Found' if gemini_api_key else '❌ Missing'}")
    
    if not gemini_api_key:
        print("\n❌ No Gemini API key found in .env file!")
        print("🔧 To get your free Gemini API key:")
        print("   1. Go to https://makersuite.google.com/app/apikey")
        print("   2. Sign in with your Google account")
        print("   3. Click 'Create API Key'")
        print("   4. Add it to your .env file as:")
        print("      GEMINI_API_KEY=your_api_key_here")
        return False
    
    try:
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test diseases
        test_diseases = [
            "Apple scab disease",
            "Tomato early blight",
            "Potato late blight"
        ]
        
        successful_tests = 0
        
        for disease in test_diseases:
            print(f"\n🔍 Testing: '{disease}'")
            
            prompt = f"""As an agricultural pathologist, provide comprehensive information about the plant disease: {disease}

Please structure your response as follows:

**Description:** 
Provide a clear, scientific description of this plant disease in 2-3 sentences.

**Causes:**
List the main causes of this disease (pathogen, environmental conditions, etc.)

**Effects:**
Describe the visible symptoms and damage this disease causes to plants

**Treatment:**
Recommend specific fungicides, treatments, or management strategies

**Prevention:**
List preventive measures to avoid this disease

Keep the information scientifically accurate and practical for farmers and gardeners."""
            
            try:
                response = model.generate_content(prompt)
                
                if response.text and len(response.text) > 100:
                    print(f"   Status: ✅ Success!")
                    print(f"   Response Length: {len(response.text)} characters")
                    print(f"   Preview: {response.text[:150]}...")
                    successful_tests += 1
                else:
                    print(f"   Status: ❌ Empty or short response")
                    
            except Exception as e:
                print(f"   Status: ❌ Error - {str(e)}")
        
        print(f"\n📊 Results: {successful_tests}/{len(test_diseases)} tests successful")
        
        if successful_tests == len(test_diseases):
            print("\n✅ Gemini API is working perfectly!")
            print("🚀 Your app will now use Gemini AI for enhanced disease information!")
        else:
            print(f"\n⚠️ Some tests failed. Check your API key and internet connection.")
            
        return successful_tests > 0
        
    except Exception as e:
        print(f"\n❌ Gemini API Error: {str(e)}")
        
        if "API_KEY_INVALID" in str(e):
            print("🔧 Your API key appears to be invalid. Please check:")
            print("   1. Make sure you copied the key correctly")
            print("   2. Verify the key is active in Google AI Studio")
            print("   3. Check for any extra spaces or characters")
        elif "PERMISSION_DENIED" in str(e):
            print("🔧 Permission denied. This might mean:")
            print("   1. API key doesn't have proper permissions")
            print("   2. Gemini API isn't enabled for your project")
            print("   3. You've exceeded the free quota")
        elif "quota" in str(e).lower():
            print("🔧 You may have exceeded the free tier limits")
            print("   1. Gemini offers 1000 requests per day free")
            print("   2. Try again tomorrow or upgrade your plan")
        
        return False

def main():
    """Main test function"""
    print("🧪 Gemini AI API Test Suite")
    print("=" * 60)
    
    success = test_gemini_api()
    
    print(f"\n{'✅' if success else '❌'} Test completed!")
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Add your Gemini API key to .env file")
        print("   2. Restart your Flask app")
        print("   3. Upload plant disease images")
        print("   4. See AI-generated disease information!")
    else:
        print("\n💡 Troubleshooting:")
        print("   1. Get your free API key from https://makersuite.google.com/app/apikey")
        print("   2. Add it to your .env file")
        print("   3. Run this test again")

if __name__ == "__main__":
    main()
