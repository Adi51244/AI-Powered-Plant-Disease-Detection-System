#!/usr/bin/env python3
"""
Test script to verify the improved response parsing functionality
"""
import re

def parse_structured_gemini_response(text, is_healthy=False):
    """Parse Gemini's structured response into clean sections"""
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
            # Parse structured response
            # Extract description first
            desc_patterns = [
                r'DESCRIPTION:\s*(.*?)(?=\s*CAUSES?:|EFFECTS?:|TREATMENT:|PREVENTION:|$)',
                r'^(.*?)(?=\s*CAUSES?:|EFFECTS?:|TREATMENT:|PREVENTION:|$)'
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    desc = match.group(1).strip()
                    if len(desc) > 50:  # Good description length
                        sections['description'] = desc
                        break
            
            # Extract sections with improved patterns
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
                    # Extract bullet points, numbered lists, or sentences
                    items = []
                    
                    # Split by common delimiters
                    lines = re.split(r'[.\n]|\d+\.|[-•]', content)
                    
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10:  # Meaningful content
                            # Clean up the line
                            clean_line = re.sub(r'^[-•\d.\s]*', '', line).strip()
                            if clean_line and len(clean_line) > 5:
                                items.append(clean_line[:250])  # Reasonable length
                    
                    sections[key] = items[:5] if items else []  # Limit to 5 items
        
        else:
            # Handle unstructured response - try to extract meaningful sections
            sentences = re.split(r'[.!?]\s+', text)
            
            # Use the full text as description, but break it into readable parts
            full_text = text
            
            # Try to identify different parts based on keywords
            causes_keywords = ['caused by', 'due to', 'infection', 'pathogen', 'fungus', 'bacteria', 'virus']
            effects_keywords = ['symptoms', 'damage', 'affects', 'reduces', 'impact', 'yield', 'production']
            treatment_keywords = ['treatment', 'control', 'manage', 'fungicide', 'spray', 'remove', 'prune']
            prevention_keywords = ['prevent', 'avoid', 'resistant', 'rotation', 'sanitation', 'hygiene']
            
            # Extract description (first part)
            sections['description'] = full_text
            
            # Try to extract causes
            causes = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in causes_keywords):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10:
                        causes.append(clean_sentence[:200])
            sections['causes'] = causes[:3]
            
            # Try to extract effects
            effects = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in effects_keywords):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10:
                        effects.append(clean_sentence[:200])
            sections['effects'] = effects[:3]
            
            # Try to extract solutions
            solutions = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in treatment_keywords):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10:
                        solutions.append(clean_sentence[:200])
            sections['solutions'] = solutions[:3]
            
            # Try to extract prevention
            prevention = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in prevention_keywords):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10:
                        prevention.append(clean_sentence[:200])
            sections['prevention'] = prevention[:3]
        
        # Ensure we have at least a description
        if not sections['description'] and text:
            sections['description'] = text[:800] if len(text) > 800 else text
            
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        # Fallback - return the full text as description
        sections['description'] = text[:1000] if len(text) > 1000 else text
    
    return sections

def test_parse_function():
    # Test with a long unstructured response (similar to what user reported)
    test_response = """DESCRIPTION: Corn rust is a fungal disease affecting corn leaves and stalks. It appears as reddish-brown pustules, reducing the plant's ability to photosynthesize and ultimately yield. Severe infections can significantly impact grain production and overall plant health. This disease is caused by fungal pathogens that thrive in warm, humid conditions and can spread rapidly through spores carried by wind and water. The disease typically manifests as small, circular to oval-shaped pustules that rupture to release reddish-brown spores. As the disease progresses, leaves may turn yellow and die prematurely, leading to reduced photosynthetic capacity and overall plant vigor. CAUSES: Infection by Puccinia sorghi fungus, warm and humid weather conditions, poor air circulation around plants, overhead irrigation that creates leaf moisture, presence of infected crop residue, and susceptible corn varieties. EFFECTS: Reduced photosynthetic area due to leaf damage, premature leaf senescence and death, decreased grain yield and quality, weakened plant structure making plants more susceptible to lodging, and potential secondary infections from other pathogens. TREATMENT: Application of fungicides containing active ingredients like propiconazole or tebuconazole, removal and destruction of infected plant debris, improving air circulation through proper plant spacing, avoiding overhead irrigation during humid periods, and using resistant corn varieties when available."""
    
    print("Testing improved parsing function...")
    print("=" * 60)
    
    # Parse the response
    parsed = parse_structured_gemini_response(test_response, is_healthy=False)
    
    # Display results
    print(f"DESCRIPTION ({len(parsed['description'])} chars):")
    print(f"  {parsed['description'][:200]}...")
    print()
    
    print(f"CAUSES ({len(parsed['causes'])} items):")
    for i, cause in enumerate(parsed['causes'], 1):
        print(f"  {i}. {cause[:100]}...")
    print()
    
    print(f"EFFECTS ({len(parsed['effects'])} items):")
    for i, effect in enumerate(parsed['effects'], 1):
        print(f"  {i}. {effect[:100]}...")
    print()
    
    print(f"SOLUTIONS ({len(parsed['solutions'])} items):")
    for i, solution in enumerate(parsed['solutions'], 1):
        print(f"  {i}. {solution[:100]}...")
    print()
    
    print(f"PREVENTION ({len(parsed['prevention'])} items):")
    for i, prevention in enumerate(parsed['prevention'], 1):
        print(f"  {i}. {prevention[:100]}...")
    print()
    
    # Test summary
    print("=" * 60)
    print("PARSING TEST RESULTS:")
    print(f"✅ Description extracted: {'YES' if parsed['description'] else 'NO'}")
    print(f"✅ Causes found: {len(parsed['causes'])} items")
    print(f"✅ Effects found: {len(parsed['effects'])} items") 
    print(f"✅ Solutions found: {len(parsed['solutions'])} items")
    print(f"✅ Prevention found: {len(parsed['prevention'])} items")
    
    return parsed

if __name__ == "__main__":
    test_parse_function()
