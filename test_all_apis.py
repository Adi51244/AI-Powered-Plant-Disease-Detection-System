#!/usr/bin/env python3
"""
Comprehensive API Test for Plant Disease Detection System
Tests PlantNet, Gemini AI, Google Search, and Wikipedia APIs
"""

import os
import sys
import requests

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

def test_all_apis():
    """Test all configured APIs"""
    print("🧪 Comprehensive API Test Suite")
    print("=" * 60)
    
    # Load environment variables
    env_vars = load_env_vars()
    
    # Test diseases
    test_diseases = [
        ("Apple scab disease", "diseased"),
        ("Tomato early blight", "diseased"), 
        ("Apple leaf", "healthy"),
        ("Tomato leaf", "healthy")
    ]
    
    # API Tests
    apis_tested = {
        'gemini': False,
        'google_search': False,
        'wikipedia': False,
        'plantnet': False
    }
    
    print(f"📋 API Keys Status:")
    print(f"   Gemini API: {'✅ Found' if env_vars.get('GEMINI_API_KEY') else '❌ Missing'}")
    print(f"   Google API: {'✅ Found' if env_vars.get('GOOGLE_API_KEY') else '❌ Missing'}")
    print(f"   PlantNet API: {'✅ Found' if env_vars.get('PLANTNET_API_KEY') else '❌ Missing'}")
    
    # Test Gemini AI
    print(f"\n🤖 Testing Gemini AI")
    print("-" * 40)
    if env_vars.get('GEMINI_API_KEY'):
        try:
            import google.generativeai as genai
            genai.configure(api_key=env_vars.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with diseased plant
            prompt = """As an agricultural pathologist, provide brief information about Apple scab disease in 100 words."""
            response = model.generate_content(prompt)
            
            if response.text:
                print(f"   ✅ Gemini AI: Working perfectly!")
                print(f"   📝 Sample response: {response.text[:100]}...")
                apis_tested['gemini'] = True
            else:
                print(f"   ❌ Gemini AI: Empty response")
                
        except Exception as e:
            print(f"   ❌ Gemini AI Error: {str(e)}")
    else:
        print(f"   ⏭️ Gemini AI: No API key configured")
    
    # Test Google Custom Search
    print(f"\n🔍 Testing Google Custom Search")
    print("-" * 40)
    google_api_key = env_vars.get('GOOGLE_API_KEY')
    google_search_id = env_vars.get('GOOGLE_SEARCH_ENGINE_ID')
    
    if google_api_key and google_search_id:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': google_search_id,
                'q': 'apple scab disease treatment',
                'num': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    print(f"   ✅ Google Search: Working perfectly!")
                    print(f"   📝 Found {len(data['items'])} results")
                    apis_tested['google_search'] = True
                else:
                    print(f"   ❌ Google Search: No results found")
            else:
                print(f"   ❌ Google Search Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Google Search Error: {str(e)}")
    else:
        print(f"   ⏭️ Google Search: No API key configured")
    
    # Test Wikipedia API
    print(f"\n📚 Testing Wikipedia API")
    print("-" * 40)
    try:
        headers = {
            'User-Agent': 'PlantDiseaseDetection/1.0 (Educational Research Project)'
        }
        
        response = requests.get(
            'https://en.wikipedia.org/api/rest_v1/page/summary/Apple_scab',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('extract'):
                print(f"   ✅ Wikipedia: Working perfectly!")
                print(f"   📝 Sample: {data['extract'][:100]}...")
                apis_tested['wikipedia'] = True
            else:
                print(f"   ❌ Wikipedia: No extract found")
        else:
            print(f"   ❌ Wikipedia Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Wikipedia Error: {str(e)}")
    
    # Test PlantNet API (requires image, so just test connectivity)
    print(f"\n🌿 Testing PlantNet API")
    print("-" * 40)
    if env_vars.get('PLANTNET_API_KEY'):
        try:
            # Test API connectivity (without image)
            test_url = "https://my-api.plantnet.org/v2/projects"
            params = {'api-key': env_vars.get('PLANTNET_API_KEY')}
            
            response = requests.get(test_url, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ PlantNet API: Key is valid and active!")
                apis_tested['plantnet'] = True
            else:
                print(f"   ❌ PlantNet API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ PlantNet API Error: {str(e)}")
    else:
        print(f"   ⏭️ PlantNet API: No API key configured")
    
    # Summary
    print(f"\n📊 API Test Results")
    print("=" * 60)
    working_apis = sum(apis_tested.values())
    total_configured = len([k for k, v in {
        'GEMINI_API_KEY': env_vars.get('GEMINI_API_KEY'),
        'GOOGLE_API_KEY': env_vars.get('GOOGLE_API_KEY'),
        'PLANTNET_API_KEY': env_vars.get('PLANTNET_API_KEY'),
        'Wikipedia': True  # Always available
    }.items() if v])
    
    print(f"✅ Working APIs: {working_apis}")
    print(f"📋 Configured APIs: {total_configured}")
    print(f"📈 Success Rate: {working_apis/4*100:.0f}%")
    
    if working_apis >= 2:
        print(f"\n🎉 Your system has multiple API sources working!")
        print(f"   🔄 API Priority: Gemini AI → Google Search → Wikipedia → Local Database")
        print(f"   🌿 PlantNet: {'Active for plant identification' if apis_tested['plantnet'] else 'Available when configured'}")
    else:
        print(f"\n⚠️ Limited API functionality. Your app will use:")
        print(f"   📚 Local database (comprehensive backup)")
        print(f"   🔧 Consider configuring more APIs for enhanced information")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Restart your Flask app")
    print(f"   2. Upload plant images to test the enhanced system")
    print(f"   3. Check API status indicator in your app")

if __name__ == "__main__":
    test_all_apis()
