import os
import google.generativeai as genai
import json

class ComicSummarizer:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("ERROR: GEMINI_API_KEY not found in environment!")
        else:
            print(f"Gemini API Key loaded: {api_key[:20]}...")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def create_comic_script(self, article_text, num_panels=4):
        """Convert news article to comic script with panels"""
        
        prompt = f"""You are a comic book writer. Convert this news article into a {num_panels}-panel comic script.

News Article:
{article_text[:2000]}

Instructions:
- Create exactly {num_panels} panels
- Each panel should have a VISUAL scene description (what we SEE)
- Keep dialogue SHORT - maximum 2 sentences per panel
- Focus on the main story elements that can be SHOWN visually
- Make it realistic and suitable for visual representation
- NO anime, NO fantasy - keep it realistic and newsworthy

Return ONLY a valid JSON object (no markdown, no code blocks) in this exact format:
{{
    "title": "Comic title here",
    "panels": [
        {{
            "panel_number": 1,
            "scene": "Description of what's happening visually",
            "dialogue": "Short punchy dialogue here",
            "characters": ["character1", "character2"]
        }},
        {{
            "panel_number": 2,
            "scene": "Description of what's happening visually",
            "dialogue": "What characters are saying",
            "characters": ["character1"]
        }}
    ]
}}
"""
        
        try:
            print("Calling Gemini API...")
            response = self.model.generate_content(prompt)
            
            print("Gemini response received")
            content = response.text
            
            # Clean up the response - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            print(f"Response content: {content[:200]}...")
            script = json.loads(content)
            
            # Ensure all panels have the required fields
            for i, panel in enumerate(script.get('panels', [])):
                if 'panel_number' not in panel:
                    panel['panel_number'] = i + 1
                if 'characters' not in panel:
                    panel['characters'] = []
                if 'dialogue' not in panel:
                    panel['dialogue'] = ''
                if 'scene' not in panel:
                    panel['scene'] = 'Scene description'
            
            return script
            
        except Exception as e:
            print(f"Error creating comic script: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_character_descriptions(self, script):
        """Generate consistent character descriptions for image generation"""
        
        # Extract all unique characters
        all_characters = set()
        for panel in script.get('panels', []):
            all_characters.update(panel.get('characters', []))
        
        if not all_characters:
            return {}
        
        prompt = f"""Create consistent visual descriptions for these characters in a comic book style:
Characters: {', '.join(all_characters)}

For each character, provide:
- Physical appearance (age, build, distinctive features)
- Clothing style
- Overall art style (realistic, cartoon, comic book)

Keep descriptions consistent across all panels. Use simple, clear descriptions suitable for image generation.

Return ONLY a valid JSON object (no markdown, no code blocks) with character names as keys and descriptions as values.

Example format:
{{
    "Character Name": "detailed visual description here",
    "Another Character": "detailed visual description here"
}}
"""
        
        try:
            print("Generating character descriptions...")
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Clean up markdown
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            descriptions = json.loads(content)
            print(f"Generated descriptions for {len(descriptions)} characters")
            return descriptions
            
        except Exception as e:
            print(f"Error generating character descriptions: {e}")
            return {}