# API Configuration for Plant Disease Detection App
# =================================================

# Toggle to enable/disable external APIs
USE_EXTERNAL_APIs = True

# API Sources Available:
# =====================

## 1. Wikipedia API (Free, No API Key Required)
# - Good for general disease information
# - Reliable and well-documented
# - No rate limits for reasonable usage

## 2. OpenAI API (Paid, API Key Required)
# - Excellent for detailed, structured information
# - Can generate custom formatted responses
# - Requires API key from https://platform.openai.com/
# - Cost: ~$0.002 per request
OPENAI_API_KEY = None  # Set your OpenAI API key here

## 3. Google Custom Search API (Free/Paid, API Key Required)
# - Good for finding agricultural extension information
# - Requires Google Cloud Console setup
# - Free tier: 100 searches per day
GOOGLE_API_KEY = None  # Set your Google API key here
GOOGLE_SEARCH_ENGINE_ID = None  # Set your custom search engine ID

## 4. Agricultural APIs (Various)
# - USDA Plant Database API
# - iNaturalist API
# - PlantNet API
# - University Extension Databases
PLANTNET_API_KEY = None  # Set your PlantNet API key here

# API Settings
API_TIMEOUT = 5  # seconds
MAX_API_RETRIES = 2

# Information Quality Ranking (Higher = Better)
API_QUALITY_RANKING = {
    'OpenAI': 10,
    'Wikipedia': 8,
    'Google Search': 7,
    'Agricultural APIs': 9,
    'Local Database': 6
}

# Fallback Strategy
# If primary API fails, try secondary APIs in order:
FALLBACK_ORDER = ['Wikipedia', 'Local Database']
