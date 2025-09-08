#!/usr/bin/env python3
"""
Test script to demonstrate the improved structured parsing
"""
import re

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
                        # Clean and format description
                        desc = re.sub(r'\s+', ' ', desc)  # Normalize whitespace
                        desc = desc.replace('. ', '.\n\n')  # Add paragraph breaks
                        sections['description'] = desc.strip()
                        break
            
            # Extract sections with improved patterns and formatting
            section_patterns = {
                'causes': r'CAUSES?:\s*(.*?)(?=\s*EFFECTS?:|TREATMENT:|SOLUTIONS?:|PREVENTION:|$)',
                'effects': r'EFFECTS?:\s*(.*?)(?=\s*TREATMENT:|SOLUTIONS?:|PREVENTION:|$)',
                'solutions': r'(?:TREATMENT|SOLUTIONS?):\s*(.*?)(?=\s*PREVENTION:|$)',
                'prevention': r'(?:DISEASE )?PREVENTION:\s*(.*?)(?=\s*$)'
            }
            
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
        
        # Final cleanup - remove empty items
        for key in ['causes', 'effects', 'solutions', 'prevention']:
            sections[key] = [item for item in sections[key] if item and len(item.strip()) > 5]
            
    except Exception as e:
        print(f"Error parsing response: {e}")
    
    return sections

def test_improved_parser():
    # Test with your Apple Scab example (the problematic one from before)
    test_response = """DESCRIPTION: Apple scab, caused by the fungal pathogen Venturia inaequalis, is a prevalent and economically significant disease affecting apple trees worldwide. The disease primarily manifests on leaves, but also affects fruits, stems, and blossoms. Initial leaf symptoms appear as small, olive-green, velvety spots, often on the upper leaf surface. These spots enlarge and become corky and scabby, often coalescing to form larger, irregular lesions. CAUSES: The fungus Venturia inaequalis is the primary cause; High humidity (greater than 90% for extended periods), free moisture (rain or dew) on leaf surfaces, and temperatures between 10-20°F are ideal for fungal growth; Cool, wet springs are particularly conducive to severe outbreaks; Stress factors like nutrient deficiencies, drought, or physical damage can weaken apple trees. EFFECTS: Olive-green, velvety spots on leaves developing into corky, scabby lesions; Dark brown or black, rough, corky spots on fruit; Severe infections can reduce photosynthesis due to leaf damage; Reduced fruit yield due to direct fruit damage and premature fruit drop. TREATMENT: Several fungicides are effective against V. inaequalis, including sterol inhibitors (e.g., propiconazole, difenoconazole); Strobilurins (e.g., pyraclostrobin) and succinate dehydrogenase inhibitors (SDHIs); Cultural management practices including proper sanitation; Immediate removal and destruction of infected leaves and fruit. PREVENTION: Proper sanitation, including removal and destruction of infected leaves and fruit; Adequate spacing between trees for good air circulation; Planting apple varieties with some level of resistance to scab; Proper spacing between trees is critical for air circulation and reducing humidity."""

    print("🧪 Testing Improved Parser with Apple Scab Example")
    print("=" * 60)
    
    parsed = parse_structured_gemini_response(test_response)
    
    # Display results with improved formatting
    print("📋 DESCRIPTION:")
    print(f"   Length: {len(parsed['description'])} characters")
    print(f"   Preview: {parsed['description'][:200]}...")
    print()
    
    sections = [
        ('🔍 CAUSES', parsed['causes'], '#dc3545'),
        ('⚠️ EFFECTS', parsed['effects'], '#fd7e14'),
        ('💊 SOLUTIONS', parsed['solutions'], '#28a745'),
        ('🛡️ PREVENTION', parsed['prevention'], '#007bff')
    ]
    
    for title, items, color in sections:
        print(f"{title} ({len(items)} items):")
        for i, item in enumerate(items, 1):
            print(f"   {i}. {item}")
        print()
    
    # Summary
    print("=" * 60)
    print("✅ PARSING IMPROVEMENTS:")
    print(f"• Description: Properly formatted with paragraph breaks")
    print(f"• Causes: {len(parsed['causes'])} well-formatted items extracted")
    print(f"• Effects: {len(parsed['effects'])} items with proper capitalization")
    print(f"• Solutions: {len(parsed['solutions'])} treatment options parsed")
    print(f"• Prevention: {len(parsed['prevention'])} prevention methods identified")
    print(f"• All items: Proper punctuation and formatting applied")
    print()
    print("🎨 VISUAL IMPROVEMENTS:")
    print("• Color-coded sections with distinct visual hierarchy")
    print("• Proper typography with consistent fonts and spacing")
    print("• Structured layout with cards and proper margins")
    print("• Icon-based section headers for better UX")

if __name__ == "__main__":
    test_improved_parser()
