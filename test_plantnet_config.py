#!/usr/bin/env python3
"""
PlantNet API Configuration Test and Setup Guide
"""

import requests
import os

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
        return {}
    return env_vars

def test_plantnet_api():
    """Test PlantNet API configuration"""
    print("🌿 PlantNet API Configuration Test")
    print("=" * 60)
    
    env_vars = load_env_vars()
    plantnet_key = env_vars.get('PLANTNET_API_KEY', '')
    
    if not plantnet_key:
        print("❌ No PlantNet API key found in .env file")
        return False
    
    print(f"📋 API Key: {'✅ Found' if plantnet_key else '❌ Missing'}")
    print(f"🔑 Key Preview: {plantnet_key[:10]}...{plantnet_key[-4:]}")
    
    # Test API connectivity
    print(f"\n🔍 Testing API Connectivity...")
    
    try:
        # Test with projects endpoint (doesn't require image)
        test_url = "https://my-api.plantnet.org/v2/projects"
        params = {'api-key': plantnet_key}
        
        print(f"📡 Calling: {test_url}")
        response = requests.get(test_url, params=params, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PlantNet API: Working perfectly!")
            print(f"📋 Available Projects: {len(data)} found")
            
            # Show available projects
            for project in data[:3]:  # Show first 3
                print(f"   • {project}")
            
            return True
            
        elif response.status_code == 401:
            print(f"❌ Authentication Error: Invalid API key")
            print(f"🔧 Check your API key in PlantNet dashboard")
            return False
            
        elif response.status_code == 403:
            print(f"❌ Permission Error: Domain/IP not authorized")
            print(f"🔧 Configure authorized domains and IPs")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error Details: {error_data}")
            except:
                print(f"📄 Raw Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        return False

def show_configuration_guide():
    """Show PlantNet API configuration guide"""
    print(f"\n🔧 PlantNet API Configuration Guide")
    print("=" * 60)
    
    print(f"📍 Go to: https://my.plantnet.org/")
    print(f"🔑 Navigate to your API key settings")
    print(f"⚙️ Configure the following:")
    
    print(f"\n🌐 Authorized Domains:")
    domains = [
        "http://localhost",
        "http://127.0.0.1", 
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://localhost",
        "https://127.0.0.1"
    ]
    
    for domain in domains:
        print(f"   • {domain}")
    
    print(f"\n🖥️ Authorized IP Addresses:")
    ips = [
        "127.0.0.1",  # localhost IPv4
        "::1",        # localhost IPv6  
        "49.37.211.148"  # Your current public IP
    ]
    
    for ip in ips:
        print(f"   • {ip}")
    
    print(f"\n💡 Additional Tips:")
    print(f"   🔹 Allow all localhost variations for development")
    print(f"   🔹 Add your public IP: 49.37.211.148")
    print(f"   🔹 If deploying later, add your server's domain/IP")
    print(f"   🔹 Save changes and wait 5-10 minutes for updates")

def main():
    """Main function"""
    print("🧪 PlantNet API Setup and Test")
    print("=" * 60)
    
    # Test current configuration
    api_working = test_plantnet_api()
    
    # Show configuration guide
    show_configuration_guide()
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 60)
    
    if api_working:
        print(f"✅ PlantNet API is working perfectly!")
        print(f"🌿 Your plant identification is ready!")
    else:
        print(f"⚠️ PlantNet API needs configuration")
        print(f"🔧 Follow the configuration guide above")
        print(f"🔄 Run this test again after configuring")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Configure domains and IPs in PlantNet dashboard")
    print(f"   2. Wait 5-10 minutes for changes to take effect")
    print(f"   3. Run: python test_plantnet_config.py")
    print(f"   4. Upload healthy plant images to test identification")

if __name__ == "__main__":
    main()
