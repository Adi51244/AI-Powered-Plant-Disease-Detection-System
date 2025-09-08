from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import os
import numpy as np
from PIL import Image
import io
import base64
import json
import requests
import re
import time
import google.generativeai as genai

# Load environment variables
def load_env_vars():
    """Load environment variables from system environment and .env file"""
    import os
    env_vars = {}
    
    # First, try to load from system environment (Render deployment)
    system_env_keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID', 'PLANTNET_API_KEY']
    for key in system_env_keys:
        value = os.getenv(key)
        if value:
            env_vars[key] = value
            print(f"✅ Loaded {key} from system environment")
    
    # Then try to load from .env file (local development)
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key not in env_vars:  # Don't overwrite system env vars
                        env_vars[key] = value
                        print(f"📁 Loaded {key} from .env file")
    except FileNotFoundError:
        print("📝 No .env file found - using system environment variables")
    
    print(f"🔑 Total environment variables loaded: {len(env_vars)}")
    return env_vars

# Load environment variables
ENV_VARS = load_env_vars()

# Get API keys from environment
GEMINI_API_KEY = ENV_VARS.get('GEMINI_API_KEY', '')
GOOGLE_API_KEY = ENV_VARS.get('GOOGLE_API_KEY', '')
GOOGLE_SEARCH_ENGINE_ID = ENV_VARS.get('GOOGLE_SEARCH_ENGINE_ID', '')
PLANTNET_API_KEY = ENV_VARS.get('PLANTNET_API_KEY', '')

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# API Configuration
USE_EXTERNAL_APIs = True  # Set to False to use only local database
API_TIMEOUT = 5  # seconds

# Create upload and results directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Load the YOLO model
MODEL_PATH = 'model/best.pt'
try:
    # Fix for PyTorch 2.8+ compatibility
    import torch.serialization
    from ultralytics.nn.tasks import DetectionModel
    torch.serialization.add_safe_globals([DetectionModel])
    model = YOLO(MODEL_PATH)
    print("✅ YOLO model loaded successfully!")
except Exception as e:
    print(f"Error loading model with safe_globals: {e}")
    # Fallback: try loading with weights_only=False (if older PyTorch)
    try:
        import torch
        original_load = torch.load
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        torch.load = patched_load
        model = YOLO(MODEL_PATH)
        torch.load = original_load
        print("✅ YOLO model loaded with fallback method!")
    except Exception as e2:
        print(f"❌ Model loading failed completely: {e2}")
        model = None

# Disease information database
DISEASE_INFO = {
    # Apple Diseases
    'Apple Scab Leaf': {
        'description': 'A common fungal disease of apple trees causing dark, scaly lesions on leaves and fruits.',
        'causes': [
            'Caused by the fungus Venturia inaequalis',
            'Thrives in cool, wet conditions (60-75°F with moisture)',
            'Overwinters in fallen leaves and releases spores in spring',
            'Spreads through rain splash and wind'
        ],
        'effects': [
            'Dark, olive-green to black spots on leaves',
            'Scaly, corky lesions on fruit',
            'Reduced fruit quality and marketability',
            'Premature leaf and fruit drop',
            'Weakened tree vigor over time'
        ],
        'solutions': [
            'Apply fungicides like captan, myclobutanil, or strobilurin-based products',
            'Remove and destroy fallen leaves in autumn',
            'Prune trees to improve air circulation',
            'Use scab-resistant apple varieties',
            'Apply dormant oil sprays in late winter'
        ],
        'prevention': [
            'Choose scab-resistant cultivars',
            'Ensure proper tree spacing for air circulation',
            'Avoid overhead watering',
            'Regular sanitation of fallen debris'
        ]
    },
    'Apple leaf': {
        'description': 'Healthy apple leaves showing normal growth and appearance.',
        'characteristics': [
            'Green, healthy foliage without disease symptoms',
            'Normal leaf structure and color',
            'Good photosynthetic activity',
            'No visible fungal, bacterial, or pest damage'
        ],
        'maintenance': [
            'Continue regular monitoring for disease symptoms',
            'Maintain proper tree nutrition and watering',
            'Ensure good air circulation through pruning',
            'Follow integrated pest management practices'
        ]
    },
    'Apple rust leaf': {
        'description': 'A fungal disease that affects apple trees, characterized by orange/yellow spots on leaves.',
        'causes': [
            'Caused by the fungus Gymnosporangium juniperi-virginianae',
            'Requires both cedar/juniper trees and apple trees to complete its life cycle',
            'Spreads through windborne spores, especially in wet conditions'
        ],
        'effects': [
            'Yellow-orange spots on upper leaf surfaces',
            'Reduced photosynthesis capacity',
            'Premature leaf drop',
            'Weakened tree health and reduced fruit quality',
            'Can lead to defoliation in severe cases'
        ],
        'solutions': [
            'Remove cedar or juniper trees within 1-2 miles if possible',
            'Apply fungicides containing myclobutanil or propiconazole',
            'Use resistant apple varieties like Liberty, Enterprise, or Pristine',
            'Ensure good air circulation around trees',
            'Clean up fallen leaves and debris regularly'
        ],
        'prevention': [
            'Plant disease-resistant apple varieties',
            'Maintain proper spacing between trees',
            'Avoid overhead irrigation',
            'Monitor weather conditions for disease-favorable periods'
        ]
    },
    
    # Bell Pepper Diseases
    'Bell_pepper leaf': {
        'description': 'Healthy bell pepper leaves with normal appearance.',
        'characteristics': [
            'Dark green, healthy foliage',
            'Normal leaf shape and size',
            'No disease symptoms visible',
            'Good plant vigor'
        ],
        'maintenance': [
            'Monitor for early disease detection',
            'Maintain consistent watering',
            'Provide adequate nutrition',
            'Ensure proper plant spacing'
        ]
    },
    'Bell_pepper leaf spot': {
        'description': 'Bacterial or fungal leaf spot disease affecting bell peppers.',
        'causes': [
            'Caused by various bacteria (Xanthomonas) or fungi',
            'Favored by warm, humid conditions',
            'Spreads through water splash and contaminated tools',
            'More severe with overhead irrigation'
        ],
        'effects': [
            'Small, dark spots on leaves',
            'Yellow halos around spots',
            'Leaf yellowing and drop',
            'Reduced fruit quality',
            'Plant defoliation in severe cases'
        ],
        'solutions': [
            'Apply copper-based bactericides',
            'Remove infected plant debris',
            'Improve air circulation',
            'Use drip irrigation instead of overhead watering',
            'Apply preventive fungicides'
        ],
        'prevention': [
            'Use certified disease-free seeds',
            'Rotate crops annually',
            'Avoid overhead watering',
            'Maintain proper plant spacing',
            'Clean tools between plants'
        ]
    },
    
    # Corn Diseases
    'Corn Gray leaf spot': {
        'description': 'A fungal disease causing rectangular gray spots on corn leaves.',
        'causes': [
            'Caused by Cercospora zeae-maydis fungus',
            'Favored by warm temperatures (80°F) and high humidity',
            'Spreads through windborne spores',
            'More severe in continuous corn fields'
        ],
        'effects': [
            'Rectangular gray lesions parallel to leaf veins',
            'Reduced photosynthetic area',
            'Premature leaf death',
            'Potential yield reduction of 15-60%',
            'Weakened stalk strength'
        ],
        'solutions': [
            'Plant resistant corn hybrids',
            'Apply fungicides containing strobilurins or triazoles',
            'Practice crop rotation with non-corn crops',
            'Tillage to bury crop residue',
            'Monitor fields during critical growth stages'
        ],
        'prevention': [
            'Use resistant varieties',
            'Rotate with soybeans or other non-host crops',
            'Bury crop residue through tillage',
            'Avoid continuous corn production'
        ]
    },
    'Corn leaf blight': {
        'description': 'Northern corn leaf blight causing cigar-shaped lesions on corn leaves.',
        'causes': [
            'Caused by Exserohilum turcicum fungus',
            'Favored by moderate temperatures (64-81°F) and high humidity',
            'Overwinters in crop residue',
            'Spreads through wind and rain splash'
        ],
        'effects': [
            'Long, cigar-shaped gray-green lesions',
            'Lesions can grow 5-6 inches long',
            'Rapid spread under favorable conditions',
            'Significant yield losses possible',
            'Reduced grain quality'
        ],
        'solutions': [
            'Plant resistant corn hybrids',
            'Apply fungicides when conditions favor disease',
            'Rotate crops to reduce inoculum',
            'Bury crop residue',
            'Monitor weather conditions'
        ],
        'prevention': [
            'Use resistant varieties',
            'Practice crop rotation',
            'Manage crop residue',
            'Time planting to avoid favorable conditions'
        ]
    },
    'Corn rust leaf': {
        'description': 'A fungal disease affecting corn plants, characterized by small, reddish-brown pustules on leaves.',
        'causes': [
            'Caused by the fungus Puccinia sorghi',
            'Favored by cool temperatures (60-70°F) and high humidity',
            'Spores spread by wind over long distances',
            'More severe in areas with dew formation'
        ],
        'effects': [
            'Small, reddish-brown pustules on both leaf surfaces',
            'Reduced photosynthetic area',
            'Premature leaf death in severe cases',
            'Potential yield reduction of 5-20%',
            'Weakened stalks susceptible to lodging'
        ],
        'solutions': [
            'Plant resistant corn hybrids',
            'Apply fungicides containing azoxystrobin or propiconazole if economically justified',
            'Monitor fields regularly during susceptible growth stages',
            'Rotate crops to reduce inoculum buildup',
            'Maintain proper plant nutrition, especially nitrogen'
        ],
        'prevention': [
            'Use resistant or tolerant corn varieties',
            'Avoid planting in areas with poor air circulation',
            'Remove crop residue after harvest',
            'Practice crop rotation with non-host plants'
        ]
    },
    
    # Potato Diseases
    'Potato leaf': {
        'description': 'Healthy potato leaves showing normal growth and appearance.',
        'characteristics': [
            'Green, vigorous foliage without spots or discoloration',
            'Strong leaf structure',
            'Normal growth patterns',
            'No visible fungal, bacterial, or viral symptoms'
        ],
        'maintenance': [
            'Continue regular monitoring for early disease detection',
            'Maintain proper irrigation and nutrition',
            'Keep fields clean of weeds and debris',
            'Follow integrated pest management practices'
        ]
    },
    'Potato leaf early blight': {
        'description': 'A fungal disease causing dark spots with concentric rings on potato leaves and tubers.',
        'causes': [
            'Caused by the fungus Alternaria solani',
            'Favored by warm temperatures (75-85°F) and high humidity',
            'Spreads through wind, rain splash, and contaminated tools',
            'More severe on stressed or older plants'
        ],
        'effects': [
            'Dark brown spots with concentric rings on leaves',
            'Yellowing and death of lower leaves first',
            'Reduced tuber size and quality',
            'Dark, sunken lesions on tubers',
            'Significant yield losses if untreated'
        ],
        'solutions': [
            'Apply fungicides containing chlorothalonil, mancozeb, or azoxystrobin',
            'Remove infected plant debris',
            'Ensure proper plant spacing and air circulation',
            'Use drip irrigation instead of overhead watering',
            'Harvest tubers when fully mature'
        ],
        'prevention': [
            'Plant certified disease-free seed potatoes',
            'Rotate crops with non-solanaceous plants',
            'Maintain proper soil drainage',
            'Avoid mechanical injury to plants',
            'Store tubers in proper conditions'
        ]
    },
    'Potato leaf late blight': {
        'description': 'A devastating disease caused by an oomycete that can destroy entire potato crops.',
        'causes': [
            'Caused by Phytophthora infestans',
            'Favored by cool, wet conditions (60-70°F)',
            'Spreads rapidly through wind and rain',
            'Can survive in infected tubers and volunteer plants'
        ],
        'effects': [
            'Water-soaked lesions on leaves and stems',
            'White fuzzy growth on leaf undersides',
            'Rapid plant death in favorable conditions',
            'Tuber rot and storage losses',
            'Complete crop destruction possible'
        ],
        'solutions': [
            'Apply protective fungicides before infection',
            'Use systemic fungicides at first sign of disease',
            'Remove and destroy infected plants',
            'Improve air circulation',
            'Harvest before tubers are infected'
        ],
        'prevention': [
            'Plant certified disease-free seed',
            'Use resistant varieties when available',
            'Monitor weather conditions closely',
            'Eliminate volunteer plants and cull piles',
            'Practice crop rotation'
        ]
    },
    
    # Tomato Diseases
    'Tomato Early blight leaf': {
        'description': 'A common fungal disease of tomatoes causing dark spots with target-like patterns on leaves.',
        'causes': [
            'Caused by the fungus Alternaria solani',
            'Favored by warm, humid conditions (75-85°F)',
            'Spreads through wind, rain splash, and contaminated tools',
            'More common on stressed or nutrient-deficient plants'
        ],
        'effects': [
            'Dark brown spots with concentric rings on lower leaves',
            'Progressive upward spread of symptoms',
            'Stem lesions and fruit rot',
            'Reduced fruit quality and yield',
            'Plant defoliation in severe cases'
        ],
        'solutions': [
            'Apply fungicides containing chlorothalonil, copper, or mancozeb',
            'Remove affected plant parts immediately',
            'Improve air circulation through proper spacing',
            'Use drip irrigation to avoid wetting foliage',
            'Apply mulch to prevent soil splash'
        ],
        'prevention': [
            'Plant resistant tomato varieties when available',
            'Rotate crops annually',
            'Maintain proper plant nutrition',
            'Avoid overhead watering',
            'Clean up plant debris at season end'
        ]
    },
    'Tomato Septoria leaf spot': {
        'description': 'A fungal disease causing small, circular spots with gray centers on tomato leaves.',
        'causes': [
            'Caused by Septoria lycopersici fungus',
            'Favored by warm, humid conditions',
            'Spreads through rain splash and wind',
            'Overwinters in plant debris'
        ],
        'effects': [
            'Small circular spots with gray centers and dark borders',
            'Spots primarily on older leaves',
            'Progressive defoliation from bottom up',
            'Reduced fruit production',
            'Weakened plant vigor'
        ],
        'solutions': [
            'Apply fungicides containing copper or chlorothalonil',
            'Remove lower leaves showing symptoms',
            'Mulch around plants to prevent soil splash',
            'Improve air circulation',
            'Water at soil level'
        ],
        'prevention': [
            'Use certified disease-free transplants',
            'Space plants properly for air circulation',
            'Remove plant debris at season end',
            'Rotate crops with non-solanaceous plants'
        ]
    },
    'Tomato leaf': {
        'description': 'Healthy tomato leaves displaying normal growth and appearance.',
        'characteristics': [
            'Dark green, healthy foliage',
            'Strong leaf development',
            'Normal leaf shape and size',
            'No disease symptoms visible'
        ],
        'maintenance': [
            'Monitor regularly for early disease signs',
            'Maintain consistent watering schedule',
            'Provide adequate nutrition',
            'Support plants properly to prevent stress'
        ]
    },
    'Tomato leaf bacterial spot': {
        'description': 'A bacterial disease causing small, dark spots on tomato leaves and fruit.',
        'causes': [
            'Caused by Xanthomonas bacteria species',
            'Spreads through water splash, wind, and contaminated tools',
            'Favored by warm, humid conditions',
            'Can survive on seeds and plant debris'
        ],
        'effects': [
            'Small, dark brown to black spots on leaves',
            'Spots may have yellow halos',
            'Leaf yellowing and defoliation',
            'Fruit spots reduce marketability',
            'Reduced plant vigor'
        ],
        'solutions': [
            'Apply copper-based bactericides',
            'Remove infected plants and debris',
            'Avoid overhead irrigation',
            'Use drip irrigation systems',
            'Disinfect tools between plants'
        ],
        'prevention': [
            'Use certified disease-free seeds and transplants',
            'Practice crop rotation',
            'Avoid working with wet plants',
            'Maintain proper plant spacing',
            'Remove plant debris after harvest'
        ]
    },
    'Tomato leaf late blight': {
        'description': 'A devastating oomycete disease that can rapidly destroy tomato plants.',
        'causes': [
            'Caused by Phytophthora infestans',
            'Favored by cool, wet conditions (60-70°F)',
            'Spreads rapidly through wind and rain',
            'Can survive in infected plant material'
        ],
        'effects': [
            'Large, irregular brown lesions on leaves',
            'White fuzzy growth on leaf undersides in humid conditions',
            'Rapid plant death in favorable weather',
            'Brown rot on fruit',
            'Complete crop loss possible'
        ],
        'solutions': [
            'Apply preventive fungicides before infection',
            'Use systemic fungicides at first symptoms',
            'Remove and destroy infected plants immediately',
            'Improve air circulation around plants',
            'Harvest fruit before infection spreads'
        ],
        'prevention': [
            'Use resistant varieties when available',
            'Monitor weather conditions for disease-favorable periods',
            'Space plants properly for air circulation',
            'Avoid overhead watering',
            'Remove volunteer tomato plants'
        ]
    },
    'Tomato leaf mosaic virus': {
        'description': 'A viral disease causing mosaic patterns and distortion on tomato leaves.',
        'causes': [
            'Caused by Tobacco Mosaic Virus (TMV) or related viruses',
            'Spreads through mechanical contact and contaminated tools',
            'Can survive in plant debris and tobacco products',
            'Transmitted through handling infected plants'
        ],
        'effects': [
            'Light and dark green mosaic patterns on leaves',
            'Leaf distortion and curling',
            'Stunted plant growth',
            'Reduced fruit production and quality',
            'Mottled fruit appearance'
        ],
        'solutions': [
            'Remove infected plants immediately',
            'Disinfect tools with 10% bleach solution',
            'Control aphids and other potential vectors',
            'Use virus-free transplants',
            'Avoid tobacco use around plants'
        ],
        'prevention': [
            'Use certified virus-free seeds and transplants',
            'Practice good sanitation',
            'Avoid smoking around plants',
            'Control insect vectors',
            'Remove plant debris promptly'
        ]
    },
    'Tomato leaf yellow virus': {
        'description': 'A viral disease transmitted by whiteflies causing severe yellowing and curling of tomato leaves.',
        'causes': [
            'Caused by Tomato Yellow Leaf Curl Virus (TYLCV)',
            'Transmitted by whitefly (Bemisia tabaci)',
            'Cannot be cured once plants are infected',
            'More severe in warm climates'
        ],
        'effects': [
            'Severe upward curling and yellowing of leaves',
            'Stunted plant growth',
            'Reduced fruit production',
            'Small, poor-quality fruits',
            'Potential complete crop loss'
        ],
        'solutions': [
            'Remove infected plants immediately to prevent spread',
            'Control whitefly populations with insecticides or biological control',
            'Use reflective mulches to repel whiteflies',
            'Install fine mesh screens in greenhouse settings',
            'Plant virus-resistant tomato varieties'
        ],
        'prevention': [
            'Use certified virus-free transplants',
            'Control whitefly populations proactively',
            'Remove weeds that can harbor the virus',
            'Use physical barriers like row covers',
            'Plant resistant varieties when available'
        ]
    },
    'Tomato mold leaf': {
        'description': 'Fungal disease causing fuzzy mold growth on tomato leaves.',
        'causes': [
            'Caused by various fungal pathogens',
            'Favored by high humidity and poor air circulation',
            'Spreads through spores in humid conditions',
            'More common in greenhouse conditions'
        ],
        'effects': [
            'Fuzzy mold growth on leaf surfaces',
            'Leaf yellowing and death',
            'Reduced photosynthesis',
            'Plant defoliation',
            'Reduced fruit quality'
        ],
        'solutions': [
            'Improve air circulation around plants',
            'Reduce humidity levels',
            'Apply appropriate fungicides',
            'Remove infected plant parts',
            'Increase plant spacing'
        ],
        'prevention': [
            'Ensure proper ventilation',
            'Avoid overhead watering',
            'Space plants adequately',
            'Monitor humidity levels',
            'Remove plant debris regularly'
        ]
    },
    'Tomato two spotted spider mites leaf': {
        'description': 'Damage caused by two-spotted spider mites feeding on tomato leaves.',
        'causes': [
            'Caused by Tetranychus urticae (two-spotted spider mites)',
            'Favored by hot, dry conditions',
            'Spreads rapidly in greenhouse conditions',
            'More severe on stressed plants'
        ],
        'effects': [
            'Stippling and yellowing of leaves',
            'Fine webbing on leaves and stems',
            'Leaf bronzing and drop',
            'Reduced plant vigor',
            'Potential plant death in severe infestations'
        ],
        'solutions': [
            'Apply miticides specifically for spider mites',
            'Use biological control agents like predatory mites',
            'Increase humidity around plants',
            'Remove heavily infested leaves',
            'Use insecticidal soaps or oils'
        ],
        'prevention': [
            'Monitor plants regularly for early detection',
            'Maintain adequate humidity levels',
            'Avoid water stress',
            'Remove weeds that can harbor mites',
            'Use beneficial insects for biological control'
        ]
    },
    
    # Other Healthy Leaves
    'Blueberry leaf': {
        'description': 'Healthy blueberry leaves with normal appearance.',
        'characteristics': [
            'Green, healthy foliage',
            'Normal leaf structure',
            'No disease symptoms',
            'Good plant vigor'
        ],
        'maintenance': [
            'Monitor for diseases and pests',
            'Maintain proper soil pH (acidic)',
            'Provide adequate water',
            'Prune for good air circulation'
        ]
    },
    'Cherry leaf': {
        'description': 'Healthy cherry tree leaves showing normal growth.',
        'characteristics': [
            'Healthy green foliage',
            'Normal leaf development',
            'No visible disease symptoms',
            'Good tree vigor'
        ],
        'maintenance': [
            'Regular monitoring for diseases',
            'Proper pruning for air circulation',
            'Adequate nutrition and watering',
            'Integrated pest management'
        ]
    },
    'Peach leaf': {
        'description': 'Healthy peach tree leaves with normal appearance.',
        'characteristics': [
            'Green, healthy foliage',
            'Normal leaf shape and size',
            'No disease symptoms visible',
            'Good tree health'
        ],
        'maintenance': [
            'Monitor for leaf curl and other diseases',
            'Maintain proper tree nutrition',
            'Ensure good air circulation',
            'Regular pruning and sanitation'
        ]
    },
    'Raspberry leaf': {
        'description': 'Healthy raspberry cane leaves showing normal growth.',
        'characteristics': [
            'Green, vigorous foliage',
            'Normal leaf structure',
            'No disease symptoms',
            'Good cane development'
        ],
        'maintenance': [
            'Monitor for diseases and pests',
            'Proper cane management',
            'Adequate water and nutrition',
            'Good air circulation'
        ]
    },
    'Soyabean leaf': {
        'description': 'Healthy soybean leaves displaying normal growth.',
        'characteristics': [
            'Green, healthy trifoliate leaves',
            'Normal leaf development',
            'No disease symptoms visible',
            'Good plant vigor'
        ],
        'maintenance': [
            'Monitor for diseases and pests',
            'Maintain proper plant nutrition',
            'Ensure adequate water',
            'Practice crop rotation'
        ]
    },
    'Squash Powdery mildew leaf': {
        'description': 'Powdery mildew disease affecting squash leaves.',
        'causes': [
            'Caused by various powdery mildew fungi',
            'Favored by warm days and cool nights',
            'High humidity promotes development',
            'Spreads through airborne spores'
        ],
        'effects': [
            'White powdery coating on leaves',
            'Leaf yellowing and death',
            'Reduced photosynthesis',
            'Stunted plant growth',
            'Reduced fruit quality and yield'
        ],
        'solutions': [
            'Apply fungicides containing sulfur or potassium bicarbonate',
            'Use systemic fungicides for severe infections',
            'Improve air circulation around plants',
            'Remove infected plant parts',
            'Apply preventive sprays'
        ],
        'prevention': [
            'Plant resistant varieties',
            'Ensure proper plant spacing',
            'Avoid overhead watering',
            'Remove plant debris',
            'Monitor humidity levels'
        ]
    },
    'Strawberry leaf': {
        'description': 'Healthy strawberry leaves showing normal growth.',
        'characteristics': [
            'Green, trifoliate leaves',
            'Normal leaf structure',
            'No disease symptoms',
            'Good plant vigor'
        ],
        'maintenance': [
            'Monitor for leaf spot diseases',
            'Maintain proper plant spacing',
            'Adequate water and nutrition',
            'Remove old leaves regularly'
        ]
    },
    'grape leaf': {
        'description': 'Healthy grape vine leaves with normal appearance.',
        'characteristics': [
            'Green, lobed leaves',
            'Normal leaf development',
            'No disease symptoms visible',
            'Good vine vigor'
        ],
        'maintenance': [
            'Monitor for fungal diseases',
            'Ensure proper air circulation',
            'Maintain adequate nutrition',
            'Regular pruning and training'
        ]
    },
    'grape leaf black rot': {
        'description': 'A serious fungal disease of grapes causing black rot on leaves and fruit.',
        'causes': [
            'Caused by Guignardia bidwellii fungus',
            'Favored by warm, humid conditions',
            'Spreads through rain splash and wind',
            'Overwinters in infected plant debris'
        ],
        'effects': [
            'Circular brown spots on leaves with dark borders',
            'Black, mummified berries',
            'Reduced grape quality and yield',
            'Defoliation in severe cases',
            'Economic losses in vineyards'
        ],
        'solutions': [
            'Apply preventive fungicides before symptoms appear',
            'Remove infected plant debris',
            'Prune for better air circulation',
            'Use systemic fungicides during growing season',
            'Harvest grapes promptly when ripe'
        ],
        'prevention': [
            'Plant resistant grape varieties',
            'Ensure proper vine spacing',
            'Remove mummified berries and infected debris',
            'Apply dormant season treatments',
            'Monitor weather conditions for disease risk'
        ]
    }
}

def get_disease_info_from_api(disease_name):
    """Get disease information from online APIs - prioritizing AI and research sources"""
    try:
        # Try Gemini AI first for comprehensive analysis
        if GEMINI_API_KEY:
            info = get_gemini_disease_info(disease_name)
            if info:
                return info
        
        # Try Google Custom Search as secondary source (university research)
        if GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
            info = search_agricultural_info(disease_name)
            if info:
                return info
        
        # Try Wikipedia API as tertiary source (basic scientific info)
        info = get_wikipedia_disease_info(disease_name)
        if info:
            return info
            
    except Exception as e:
        print(f"API error: {str(e)}")
    
    # Return None to use local database
    return None

def get_wikipedia_disease_info(disease_name):
    """Get disease information from Wikipedia API"""
    try:
        # Use proper headers to avoid being blocked
        headers = {
            'User-Agent': 'PlantDiseaseDetection/1.0 (Educational Research Project)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Create multiple search strategies
        search_terms = []
        
        # Strategy 1: Clean the disease name
        clean_name = disease_name.replace(" leaf", "").replace("_", " ")
        search_terms.append(clean_name)
        
        # Strategy 2: Map specific diseases to general terms
        disease_mapping = {
            'Apple rust leaf': ['Cedar-apple_rust', 'Apple_scab', 'Gymnosporangium_juniperi-virginianae'],
            'Apple Scab Leaf': ['Apple_scab', 'Venturia_inaequalis'],
            'Tomato leaf late blight': ['Phytophthora_infestans', 'Late_blight'],
            'Tomato Early blight leaf': ['Alternaria_solani', 'Early_blight'],
            'Potato leaf early blight': ['Alternaria_solani', 'Early_blight'],
            'Potato leaf late blight': ['Phytophthora_infestans', 'Late_blight'],
            'Corn rust leaf': ['Corn_rust', 'Puccinia_sorghi'],
            'Corn Gray leaf spot': ['Gray_leaf_spot', 'Cercospora_zeae-maydis'],
            'Corn leaf blight': ['Northern_corn_leaf_blight', 'Exserohilum_turcicum'],
            'Tomato leaf yellow virus': ['Tomato_yellow_leaf_curl_virus', 'TYLCV'],
            'Tomato leaf mosaic virus': ['Tobacco_mosaic_virus', 'TMV'],
            'grape leaf black rot': ['Black_rot', 'Guignardia_bidwellii'],
            'Bell_pepper leaf spot': ['Bacterial_leaf_spot', 'Xanthomonas_campestris'],
            'Squash Powdery mildew leaf': ['Powdery_mildew', 'Podosphaera_xanthii'],
            'Tomato leaf bacterial spot': ['Bacterial_spot', 'Xanthomonas_campestris']
        }
        
        # Add mapped terms
        if disease_name in disease_mapping:
            search_terms.extend(disease_mapping[disease_name])
        
        # Strategy 3: Add generic plant disease terms
        plant_type = disease_name.split()[0].lower()
        if plant_type in ['apple', 'tomato', 'potato', 'corn', 'grape']:
            search_terms.extend([
                f"{plant_type}_disease",
                f"{plant_type}_pathology"
            ])
        
        # Strategy 4: Add common disease terms
        if 'rust' in disease_name.lower():
            search_terms.extend(['Plant_rust', 'Rust_(fungus)'])
        if 'blight' in disease_name.lower():
            search_terms.extend(['Plant_blight', 'Blight'])
        if 'scab' in disease_name.lower():
            search_terms.extend(['Plant_scab', 'Scab_(plant_disease)'])
        if 'spot' in disease_name.lower():
            search_terms.extend(['Leaf_spot', 'Bacterial_leaf_spot'])
        
        for term in search_terms:
            try:
                # Search Wikipedia with proper headers
                search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
                response = requests.get(f"{search_url}{term}", headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    description = data.get('extract', '')
                    
                    if len(description) > 100:  # Good description found
                        print(f"✅ Found Wikipedia info for: {term}")
                        
                        return {
                            'description': description,
                            'causes': ['Refer to description above for detailed pathogen information'],
                            'effects': ['Refer to description above for symptom details'],
                            'solutions': ['Consult agricultural extension services for treatment protocols'],
                            'prevention': ['Follow integrated pest management practices', 'Use disease-resistant varieties'],
                            'source': f'Wikipedia API ({data.get("title", term)})',
                            'is_structured': False  # Wikipedia provides unstructured data
                        }
            except Exception as e:
                print(f"Wikipedia search failed for {term}: {str(e)}")
                continue
                
            # Be respectful to Wikipedia servers
            time.sleep(0.5)
                
    except Exception as e:
        print(f"Wikipedia API error: {str(e)}")
    
    return None

def search_agricultural_info(disease_name):
    """Search for agricultural information using Google Custom Search API"""
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    
    try:
        # Google Custom Search API
        search_url = "https://www.googleapis.com/customsearch/v1"
        
        # Create targeted search queries
        search_queries = [
            f"{disease_name} plant disease treatment prevention",
            f"{disease_name} agricultural management control",
            f"{disease_name} fungicide pesticide solution"
        ]
        
        for query in search_queries:
            try:
                params = {
                    'key': GOOGLE_API_KEY,
                    'cx': GOOGLE_SEARCH_ENGINE_ID,
                    'q': query,
                    'num': 3,
                    'fields': 'items(title,snippet,link)'
                }
                
                print(f"🔍 Searching Google for: {query}")
                response = requests.get(search_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    
                    if items:
                        # Combine information from search results
                        descriptions = []
                        all_text = ""
                        
                        for item in items:
                            title = item.get('title', '')
                            snippet = item.get('snippet', '')
                            descriptions.append(f"{title}: {snippet}")
                            all_text += f" {title} {snippet}"
                        
                        # Create description from first few results
                        description = '. '.join(descriptions[:2])
                        
                        if len(description) > 50:  # Good information found
                            print(f"✅ Found Google search results for: {query}")
                            return {
                                'description': description,
                                'causes': ['Check university extension sources for detailed pathogen information'],
                                'effects': ['Refer to agricultural research sources for symptom identification'],
                                'solutions': ['Consult extension services for research-based treatment protocols'],
                                'prevention': ['Follow university recommendations for integrated management'],
                                'source': f'Google Custom Search API',
                                'is_structured': False  # Google provides unstructured snippets
                            }
                
                elif response.status_code == 429:
                    print("⏰ Google API rate limit reached")
                    break
                else:
                    print(f"❌ Google API error: {response.status_code}")
                
                # Respect rate limits
                time.sleep(1)
                
            except Exception as e:
                print(f"Google search error for '{query}': {str(e)}")
                continue
        
    except Exception as e:
        print(f"Google search error: {str(e)}")
    
    return None

def get_gemini_disease_info(disease_name):
    """Get AI-generated disease information from Google Gemini"""
    try:
        if not GEMINI_API_KEY:
            return None
            
        # Configure Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Check if it's a healthy plant
        is_healthy = ('leaf' in disease_name.lower() and 
                     not any(disease_term in disease_name.lower() 
                           for disease_term in ['blight', 'rust', 'spot', 'rot', 'scab', 'mosaic', 'virus', 'bacterial']))
        
        if is_healthy:
            # Create a prompt for healthy plants
            plant_type = disease_name.split()[0] if ' ' in disease_name else disease_name.replace('leaf', '').replace('_', '').strip()
            prompt = f"""As a plant expert, provide information about healthy {plant_type} plants in exactly this format:

DESCRIPTION: Write 2-3 sentences about what healthy {plant_type} plants look like.

GROWING CONDITIONS: List 3-4 optimal growing conditions.

CHARACTERISTICS: List 3-4 visual characteristics of healthy {plant_type}.

MAINTENANCE: List 3-4 care practices.

DISEASE PREVENTION: List 3-4 preventive measures.

Use simple, clear language for farmers."""
        else:
            # Create a detailed prompt for diseased plants
            prompt = f"""As an agricultural pathologist, provide comprehensive information about {disease_name} in exactly this format:

DESCRIPTION: Write a detailed paragraph (at least 100 words) about this plant disease, including its appearance, symptoms, affected plant parts, pathogen type, and how it manifests on the plant. Be thorough and complete.

CAUSES: List the main causes of this disease:
- Primary pathogen or environmental factor
- Environmental conditions that favor development
- Plant stress factors that contribute
- Transmission methods

EFFECTS: List the visible symptoms and impacts:
- Visible symptoms on leaves, stems, fruits
- Impact on plant growth and development
- Effects on crop yield and quality
- Long-term consequences if untreated

TREATMENT: List specific treatment options:
- Recommended fungicides or bactericides
- Cultural management practices
- Immediate action steps for infected plants
- Organic treatment alternatives

PREVENTION: List preventive measures:
- Best practices for disease prevention
- Resistant varieties if available
- Proper sanitation and hygiene practices
- Crop rotation and spacing recommendations

Provide complete, detailed information in each section. Do not truncate any section."""

        # Generate response
        response = model.generate_content(prompt)
        
        if response.text and len(response.text) > 100:
            print(f"✅ Found Gemini AI info for: {disease_name}")
            
            # Parse the structured response
            parsed_info = parse_structured_gemini_response(response.text, is_healthy)
            
            return {
                'description': parsed_info.get('description', response.text),
                'source': 'Gemini AI',
                'causes': parsed_info.get('causes', ['Information provided in description above']),
                'effects': parsed_info.get('effects', ['Information provided in description above']),
                'solutions': parsed_info.get('solutions', ['Information provided in description above']),
                'prevention': parsed_info.get('prevention', ['Information provided in description above']),
                'is_structured': True  # Flag to indicate this is clean API data
            }
    
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
    
    return None

def parse_structured_gemini_response(text, is_healthy=False):
    """Parse Gemini's structured response into clean, well-formatted sections"""
    sections = {
        'description': '',
        'causes': [],
        'effects': [],
        'solutions': [],
        'prevention': []
    }
    
    try:
        # Clean the text
        text = text.replace('*', '').replace('#', '').strip()
        
        # Check if response has structured format
        has_sections = any(keyword in text.upper() for keyword in 
                          ['CAUSES:', 'EFFECTS:', 'TREATMENT:', 'PREVENTION:', 'SOLUTIONS:'])
        
        if has_sections:
            # Parse structured response with improved formatting
            
            # Extract description first - handle multiple patterns
            desc_patterns = [
                r'DESCRIPTION:\s*(.*?)(?=\s*CAUSES?:|EFFECTS?:|TREATMENT:|PREVENTION:|$)',
                r'^(.*?)(?=\s*CAUSES?:|EFFECTS?:|TREATMENT:|PREVENTION:|$)'
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    desc = match.group(1).strip()
                    if len(desc) > 50:  # Good description length
                        # Clean and format description with reduced line spacing
                        desc = re.sub(r'\s+', ' ', desc)  # Normalize whitespace
                        desc = desc.replace('. ', '.\n')  # Add single line breaks instead of double
                        sections['description'] = desc.strip()
                        break
            
            # Extract sections with improved patterns and formatting
            section_patterns = {
                'causes': r'CAUSES?:\s*(.*?)(?=\s*EFFECTS?:|TREATMENT:|SOLUTIONS?:|PREVENTION:|$)',
                'effects': r'EFFECTS?:\s*(.*?)(?=\s*TREATMENT:|SOLUTIONS?:|PREVENTION:|$)',
                'solutions': r'(?:TREATMENT|SOLUTIONS?):\s*(.*?)(?=\s*PREVENTION:|$)',
                'prevention': r'(?:DISEASE )?PREVENTION:\s*(.*?)(?=\s*$)'
            }
            
            if is_healthy:
                section_patterns.update({
                    'causes': r'(?:GROWING CONDITIONS|CONDITIONS):\s*(.*?)(?=\s*CHARACTERISTICS:|MAINTENANCE:|PREVENTION:|$)',
                    'effects': r'CHARACTERISTICS:\s*(.*?)(?=\s*MAINTENANCE:|PREVENTION:|$)',
                    'solutions': r'(?:MAINTENANCE|CARE):\s*(.*?)(?=\s*PREVENTION:|$)'
                })
            
            for key, pattern in section_patterns.items():
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    items = []
                    
                    # Multiple parsing strategies for different formats
                    
                    # Strategy 1: Look for explicit bullet points or numbered lists
                    bullet_patterns = [
                        r'[-•]\s*([^-•\n]+(?:\n(?![-•])[^\n]*)*)',  # Bullet points
                        r'\d+\.\s*([^\d\n]+(?:\n(?!\d+\.)[^\n]*)*)',  # Numbered lists
                    ]
                    
                    found_items = []
                    for bullet_pattern in bullet_patterns:
                        matches = re.findall(bullet_pattern, content, re.MULTILINE)
                        if matches:
                            found_items.extend(matches)
                    
                    # Strategy 2: Split by sentences if no clear formatting
                    if not found_items:
                        # Split by common sentence delimiters
                        sentences = re.split(r'[.;]\s+(?=[A-Z])', content)
                        found_items = [s.strip() for s in sentences if len(s.strip()) > 15]
                    
                    # Strategy 3: Split by semicolons or line breaks
                    if not found_items:
                        parts = re.split(r'[;\n]+', content)
                        found_items = [p.strip() for p in parts if len(p.strip()) > 10]
                    
                    # Clean and format items
                    for item in found_items[:5]:  # Limit to 5 items
                        # Clean the item
                        clean_item = re.sub(r'^[-•\d.\s]*', '', item).strip()
                        clean_item = re.sub(r'\s+', ' ', clean_item)  # Normalize whitespace
                        
                        if len(clean_item) > 5:
                            # Ensure proper capitalization
                            clean_item = clean_item[0].upper() + clean_item[1:] if clean_item else ''
                            
                            # Ensure proper ending punctuation
                            if clean_item and not clean_item.endswith(('.', '!', '?', ':')):
                                clean_item += '.'
                            
                            items.append(clean_item[:300])  # Reasonable length limit
                    
                    sections[key] = items if items else []
        
        else:
            # Handle unstructured response with intelligent parsing
            sentences = re.split(r'[.!?]\s+', text)
            
            # Clean and format the full text as description
            full_desc = re.sub(r'\s+', ' ', text).strip()
            full_desc = full_desc.replace('. ', '.\n')  # Add single line breaks instead of double
            sections['description'] = full_desc
            
            # Intelligent keyword-based extraction
            causes_keywords = ['caused by', 'due to', 'infection', 'pathogen', 'fungus', 'bacteria', 'virus', 'environmental']
            effects_keywords = ['symptoms', 'damage', 'affects', 'reduces', 'impact', 'yield', 'production', 'lesions']
            treatment_keywords = ['treatment', 'control', 'manage', 'fungicide', 'spray', 'remove', 'prune', 'apply']
            prevention_keywords = ['prevent', 'avoid', 'resistant', 'rotation', 'sanitation', 'hygiene', 'spacing']
            
            # Extract and format sections based on keywords
            keyword_sections = [
                ('causes', causes_keywords),
                ('effects', effects_keywords),
                ('solutions', treatment_keywords),
                ('prevention', prevention_keywords)
            ]
            
            for section_name, keywords in keyword_sections:
                section_items = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if any(keyword in sentence.lower() for keyword in keywords) and len(sentence) > 20:
                        # Clean and format
                        clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                        clean_sentence = clean_sentence[0].upper() + clean_sentence[1:] if clean_sentence else ''
                        
                        if not clean_sentence.endswith(('.', '!', '?', ':')):
                            clean_sentence += '.'
                            
                        section_items.append(clean_sentence[:250])
                
                sections[section_name] = section_items[:3]  # Limit to 3 items
        
        # Ensure we have at least a description
        if not sections['description'] and text:
            clean_text = re.sub(r'\s+', ' ', text).strip()
            clean_text = clean_text.replace('. ', '.\n')  # Single line breaks
            sections['description'] = clean_text[:1000] if len(clean_text) > 1000 else clean_text
            
        # Final cleanup - remove empty items
        for key in ['causes', 'effects', 'solutions', 'prevention']:
            sections[key] = [item for item in sections[key] if item and len(item.strip()) > 5]
            
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        # Fallback - return cleaned text as description
        clean_text = re.sub(r'\s+', ' ', text).strip() if text else ''
        sections['description'] = clean_text[:1000] if len(clean_text) > 1000 else clean_text
    
    return sections

def get_plantnet_disease_info(disease_name, image_path=None):
    """Get plant identification from PlantNet API"""
    try:
        if not PLANTNET_API_KEY:
            return None
        
        # PlantNet API endpoint
        url = "https://my-api.plantnet.org/v2/identify/weurope"
        
        if image_path and os.path.exists(image_path):
            # Prepare the image for PlantNet
            files = [
                ('images', (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')),
                ('modifiers', (None, "crops")),
                ('modifiers', (None, "similar_images")),
                ('api-key', (None, PLANTNET_API_KEY))
            ]
            
            # Send request to PlantNet
            response = requests.post(url, files=files, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data and len(data['results']) > 0:
                    # Get the most likely plant identification
                    best_match = data['results'][0]
                    plant_name = best_match['species']['scientificNameWithoutAuthor']
                    common_names = [name['value'] for name in best_match['species']['commonNames'][:3]]
                    confidence = best_match['score']
                    
                    print(f"✅ PlantNet identified: {plant_name} (confidence: {confidence:.2f})")
                    
                    # Create a comprehensive plant identification response
                    description = f"Plant identified as {plant_name}"
                    if common_names:
                        description += f" (commonly known as {', '.join(common_names)})"
                    description += f" with {confidence:.1%} confidence using PlantNet's plant identification database."
                    
                    return {
                        'description': description,
                        'source': f'PlantNet Plant Identification',
                        'plant_name': plant_name,
                        'common_names': common_names,
                        'confidence': confidence,
                        'causes': [f'Scientific name: {plant_name}', f'Common names: {", ".join(common_names) if common_names else "Not available"}'],
                        'effects': [f'Identification confidence: {confidence:.1%}', 'Properly identified plant for accurate care'],
                        'solutions': ['Monitor plant health regularly', 'Follow species-specific care guidelines'],
                        'prevention': ['Use correct identification for targeted disease prevention', 'Research species-specific diseases'],
                        'is_structured': True  # PlantNet provides structured identification data
                    }
            else:
                print(f"PlantNet API error: {response.status_code}")
                
    except Exception as e:
        print(f"PlantNet API error: {str(e)}")
    
    return None

def extract_causes_from_text(text):
    """Extract disease causes from text using pattern matching"""
    causes = []
    
    # Common patterns for disease causes
    patterns = [
        r'caused by ([^.]+)',
        r'due to ([^.]+)',
        r'results from ([^.]+)',
        r'pathogen[:\s]+([^.]+)',
        r'fungus[:\s]+([^.]+)',
        r'bacteria[:\s]+([^.]+)',
        r'virus[:\s]+([^.]+)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match.strip()) > 10:
                causes.append(match.strip().capitalize())
    
    # Add common causes if none found
    if not causes:
        if 'fungal' in text_lower or 'fungus' in text_lower:
            causes.append('Fungal infection from environmental pathogens')
        if 'bacterial' in text_lower or 'bacteria' in text_lower:
            causes.append('Bacterial infection through wounds or natural openings')
        if 'viral' in text_lower or 'virus' in text_lower:
            causes.append('Viral transmission through vectors or mechanical means')
        if 'environmental' in text_lower or 'weather' in text_lower:
            causes.append('Environmental stress and weather conditions')
    
    return causes[:3] if causes else ['Pathogenic infection', 'Environmental factors', 'Plant stress conditions']

def extract_effects_from_text(text):
    """Extract disease effects from text"""
    effects = []
    
    # Common patterns for effects
    patterns = [
        r'symptoms include ([^.]+)',
        r'causes ([^.]+) in plants',
        r'results in ([^.]+)',
        r'leads to ([^.]+)',
        r'damage[:\s]+([^.]+)',
        r'affects ([^.]+)',
        r'reduces ([^.]+)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match.strip()) > 10:
                effects.append(match.strip().capitalize())
    
    # Look for common effect keywords
    effect_keywords = ['yellowing', 'spots', 'lesions', 'wilting', 'blight', 'rot', 'stunting', 'defoliation']
    for keyword in effect_keywords:
        if keyword in text_lower:
            effects.append(f'Development of {keyword} symptoms on plant tissues')
    
    return effects[:4] if effects else ['Visible symptoms on leaves and stems', 'Reduced plant vigor', 'Potential yield losses', 'Quality degradation']

def extract_solutions_from_text(text):
    """Extract treatment solutions from text"""
    solutions = []
    
    # Common patterns for solutions
    patterns = [
        r'treatment[:\s]+([^.]+)',
        r'control[:\s]+([^.]+)',
        r'management[:\s]+([^.]+)',
        r'fungicide[:\s]+([^.]+)',
        r'spray[:\s]+([^.]+)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match.strip()) > 10:
                solutions.append(match.strip().capitalize())
    
    # Add standard solutions
    if 'fungal' in text_lower or 'fungus' in text_lower:
        solutions.append('Apply appropriate fungicides as preventive or curative treatment')
    if 'bacterial' in text_lower:
        solutions.append('Use copper-based bactericides or antibiotics where permitted')
    if 'cultural' in text_lower or 'management' in text_lower:
        solutions.append('Implement cultural management practices and sanitation')
    
    return solutions[:4] if solutions else ['Apply targeted chemical treatments', 'Remove infected plant material', 'Improve cultural practices', 'Consult agricultural extension services']

def extract_prevention_from_text(text):
    """Extract prevention methods from text"""
    prevention = []
    
    # Common patterns for prevention
    patterns = [
        r'prevent[a-z]*[:\s]+([^.]+)',
        r'avoid[a-z]*[:\s]+([^.]+)',
        r'resistance[:\s]+([^.]+)',
        r'rotation[:\s]+([^.]+)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match.strip()) > 10:
                prevention.append(match.strip().capitalize())
    
    # Add standard prevention methods
    prevention_keywords = ['resistant', 'rotation', 'sanitation', 'drainage', 'spacing']
    for keyword in prevention_keywords:
        if keyword in text_lower:
            if keyword == 'resistant':
                prevention.append('Use disease-resistant plant varieties when available')
            elif keyword == 'rotation':
                prevention.append('Practice crop rotation with non-host plants')
            elif keyword == 'sanitation':
                prevention.append('Maintain field sanitation and remove plant debris')
            elif keyword == 'drainage':
                prevention.append('Ensure proper drainage to avoid waterlogged conditions')
            elif keyword == 'spacing':
                prevention.append('Provide adequate plant spacing for air circulation')
    
    return prevention[:4] if prevention else ['Use certified disease-free planting material', 'Practice integrated pest management', 'Monitor environmental conditions', 'Maintain proper plant nutrition']

def get_disease_info(disease_name, use_api=True):
    """Get detailed information about a specific disease"""
    
    # Try to get information from APIs first if enabled
    if use_api:
        api_info = get_disease_info_from_api(disease_name)
        if api_info:
            return api_info
    
    # Fallback to local database
    local_info = DISEASE_INFO.get(disease_name, {
        'description': f'Disease information for {disease_name} not available in local database.',
        'causes': ['Information not available - consult plant pathologist'],
        'effects': ['Information not available - monitor plant symptoms'],
        'solutions': ['Consult with local agricultural extension services', 'Apply general disease management practices', 'Seek professional diagnosis'],
        'prevention': ['Follow general plant health practices', 'Use integrated pest management', 'Monitor crops regularly'],
        'source': 'Local Database'
    })
    
    return local_info

def process_image(image_path):
    """Process image with YOLO model and return results"""
    try:
        # Check if model loaded successfully
        if model is None:
            raise Exception("YOLO model not loaded properly")
            
        # Run inference
        results = model(image_path)
        
        # Extract detection information
        detections = []
        
        if len(results) > 0:
            result = results[0]
            
            # Get class names
            names = result.names
            
            # Process detections
            if result.boxes is not None:
                boxes = result.boxes
                for i, box in enumerate(boxes):
                    # Get class ID and confidence
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Get class name
                    class_name = names.get(class_id, f"Unknown_{class_id}")
                    
                    # Get bounding box coordinates
                    coords = box.xyxy[0].tolist()
                    
                    detections.append({
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': coords
                    })
            
            # Save annotated image
            annotated_image = result.plot()
            result_path = os.path.join(app.config['RESULTS_FOLDER'], 'annotated_' + os.path.basename(image_path))
            cv2.imwrite(result_path, annotated_image)
            
            return detections, result_path
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return [], None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            # Save uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            print(f"🔄 Processing image: {filename}")
            
            # Process image
            detections, result_path = process_image(file_path)
            print(f"✅ Image processed successfully")
            
            # Prepare response
            response_data = {
                'detections': [],
            'result_image': None
        }
        
        if result_path and os.path.exists(result_path):
            response_data['result_image'] = f'/results/{os.path.basename(result_path)}'
        
        # Add disease information for each detection
        for detection in detections:
            disease_name = detection['class_name']
            
            # Check if it's a healthy plant (contains "leaf" without disease terms)
            is_healthy = ('leaf' in disease_name.lower() and 
                         not any(disease_term in disease_name.lower() 
                               for disease_term in ['blight', 'rust', 'spot', 'rot', 'scab', 'mosaic', 'virus', 'bacterial']))
            
            if is_healthy:
                # For healthy plants, try PlantNet identification first
                if PLANTNET_API_KEY:
                    plantnet_info = get_plantnet_disease_info(disease_name, file_path)
                    if plantnet_info:
                        disease_info = plantnet_info
                    else:
                        disease_info = get_disease_info(disease_name, use_api=USE_EXTERNAL_APIs)
                else:
                    disease_info = get_disease_info(disease_name, use_api=USE_EXTERNAL_APIs)
            else:
                # For diseased plants, use the normal API flow
                disease_info = get_disease_info(disease_name, use_api=USE_EXTERNAL_APIs)
            
            response_data['detections'].append({
                'disease': disease_name,
                'confidence': detection['confidence'],
                'info': disease_info,
                'is_healthy': is_healthy
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your image. Please try again.'}), 500

@app.route('/api/status')
def api_status():
    """Check API availability status"""
    import os
    status = {
        'external_apis_enabled': USE_EXTERNAL_APIs,
        'yolo_model': 'Loaded' if model is not None else 'Failed to load',
        'wikipedia_api': 'Available',
        'google_custom_search': 'Configured' if os.getenv('GOOGLE_API_KEY') else 'Not configured - Add GOOGLE_API_KEY env var',
        'gemini_ai': 'Configured' if os.getenv('GEMINI_API_KEY') else 'Not configured - Add GEMINI_API_KEY env var',
        'plantnet_api': 'Configured' if os.getenv('PLANTNET_API_KEY') else 'Not configured - Add PLANTNET_API_KEY env var',
        'local_database': 'Available',
        'total_diseases_in_db': len(DISEASE_INFO),
        'environment_check': {
            'GEMINI_API_KEY': 'Set' if os.getenv('GEMINI_API_KEY') else 'Missing',
            'GOOGLE_API_KEY': 'Set' if os.getenv('GOOGLE_API_KEY') else 'Missing',
            'GOOGLE_SEARCH_ENGINE_ID': 'Set' if os.getenv('GOOGLE_SEARCH_ENGINE_ID') else 'Missing',
            'PLANTNET_API_KEY': 'Set' if os.getenv('PLANTNET_API_KEY') else 'Missing'
        }
    }
    
    # Test Wikipedia API
    try:
        response = requests.get('https://en.wikipedia.org/api/rest_v1/page/summary/Plant_disease', timeout=3)
        status['wikipedia_api'] = 'Available' if response.status_code == 200 else 'Unavailable'
    except:
        status['wikipedia_api'] = 'Unavailable'
    
    # Check Google API
    if GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
        status['google_custom_search'] = 'Configured and Ready'
    
    # Check Gemini API
    if GEMINI_API_KEY:
        status['gemini_ai'] = 'Configured and Ready'
    
    # Check PlantNet API
    if PLANTNET_API_KEY:
        status['plantnet_api'] = 'Configured and Ready'
    
    return jsonify(status)

@app.route('/results/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/uploads/<filename>')
def uploaded_original(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
