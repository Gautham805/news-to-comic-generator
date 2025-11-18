import os
import requests
from pathlib import Path
import time
from huggingface_hub import InferenceClient

class ComicImageGenerator:
    def __init__(self):
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN')
        if self.hf_token:
            self.client = InferenceClient(token=self.hf_token)
            print("✓ Hugging Face client initialized")
        else:
            self.client = None
            print("⚠ No Hugging Face token - will use fallback")
        
        self.style = "comic book illustration, professional comic art, clear lines, vibrant colors, graphic novel style, detailed, high quality"
    
    def generate_with_huggingface(self, prompt):
        """Generate image using Hugging Face Stable Diffusion"""
        if not self.client:
            raise Exception("No Hugging Face token available")
        
        try:
            # Using Stable Diffusion XL model (free on HF)
            image = self.client.text_to_image(
                prompt,
                model="stabilityai/stable-diffusion-xl-base-1.0"
            )
            return image
        except Exception as e:
            print(f"Hugging Face error: {e}")
            raise
    
    def generate_with_flux(self, prompt):
        """Try Flux Schnell (faster, free model)"""
        try:
            image = self.client.text_to_image(
                prompt,
                model="black-forest-labs/FLUX.1-schnell"
            )
            return image
        except Exception as e:
            print(f"Flux error: {e}")
            raise
    
    def generate_panel_image(self, panel, character_descriptions, panel_number, output_dir='static/comics'):
        """Generate image for a single comic panel"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        scene = panel.get('scene', '')
        characters = panel.get('characters', [])
        
        # Build detailed comic-style prompt
        char_details = ""
        if characters and character_descriptions:
            for char in characters[:2]:  # Limit to 2 main characters for clarity
                if char in character_descriptions:
                    char_details += f"{char}: {character_descriptions[char][:100]}. "
        
        # Enhanced prompt for comic style
        prompt = f"{self.style}. {char_details} Scene: {scene[:200]}. Single comic book panel, dramatic composition, no text or speech bubbles in image."
        
        filename = f"panel_{panel_number}.png"
        filepath = os.path.join(output_dir, filename)
        
        print(f"🎨 Generating panel {panel_number}...")
        print(f"   Scene: {scene[:60]}...")
        
        # Try Hugging Face models
        if self.client:
            for model_name in ["Flux", "Stable Diffusion"]:
                try:
                    if model_name == "Flux":
                        image = self.generate_with_flux(prompt)
                    else:
                        image = self.generate_with_huggingface(prompt)
                    
                    # Save the PIL Image
                    image.save(filepath)
                    print(f"   ✓ Panel {panel_number} generated with {model_name}")
                    return filepath
                    
                except Exception as e:
                    print(f"   ✗ {model_name} failed: {str(e)[:50]}")
                    continue
        
        # If all else fails, create a better-looking placeholder
        print(f"   ⚠ Creating styled placeholder for panel {panel_number}")
        self.create_comic_placeholder(panel_number, scene, panel.get('dialogue', ''), filepath)
        return filepath
    
    def create_comic_placeholder(self, panel_number, scene, dialogue, filepath):
        """Create a comic-style placeholder that actually looks decent"""
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Create image with comic paper texture (light cream)
        img = Image.new('RGB', (1024, 1024), (255, 250, 240))
        draw = ImageDraw.Draw(img)
        
        # Draw comic panel border (thick black)
        border_width = 15
        draw.rectangle(
            [border_width, border_width, 1024-border_width, 1024-border_width],
            outline='black',
            width=border_width
        )
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            scene_font = ImageFont.truetype("arial.ttf", 32)
            dialogue_font = ImageFont.truetype("arialbd.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            scene_font = ImageFont.load_default()
            dialogue_font = ImageFont.load_default()
        
        # Add panel number in comic style
        draw.text((50, 50), f"PANEL {panel_number}", fill='#FF4444', font=title_font)
        
        # Add scene description with word wrap
        y_offset = 180
        wrapper = textwrap.TextWrapper(width=35)
        scene_lines = wrapper.wrap(scene)
        
        for line in scene_lines[:8]:
            draw.text((60, y_offset), line, fill='#333333', font=scene_font)
            y_offset += 45
        
        # Add dialogue in comic speech bubble style
        if dialogue:
            # Draw speech bubble background
            bubble_y = 1024 - 300
            draw.ellipse([100, bubble_y, 924, bubble_y + 250], fill='white', outline='black', width=5)
            
            # Add dialogue text
            dialogue_wrapper = textwrap.TextWrapper(width=30)
            dialogue_lines = dialogue_wrapper.wrap(dialogue)
            
            dialogue_y = bubble_y + 60
            for line in dialogue_lines[:4]:
                # Center the text
                bbox = draw.textbbox((0, 0), line, font=dialogue_font)
                text_width = bbox[2] - bbox[0]
                text_x = (1024 - text_width) // 2
                draw.text((text_x, dialogue_y), line, fill='#000000', font=dialogue_font)
                dialogue_y += 40
        
        img.save(filepath)
    
    def generate_all_panels(self, script, character_descriptions, comic_id):
        """Generate images for all panels in the script"""
        
        output_dir = f'static/comics/{comic_id}'
        panel_images = []
        
        panels = script.get('panels', [])
        print(f"\n🎬 Generating {len(panels)} comic panels...")
        
        for i, panel in enumerate(panels):
            panel_number = panel.get('panel_number', i + 1)
            
            # Small delay between API calls
            if i > 0 and self.client:
                time.sleep(2)
            
            filepath = self.generate_panel_image(
                panel, 
                character_descriptions, 
                panel_number,
                output_dir
            )
            
            if filepath:
                panel_images.append({
                    'panel_number': panel_number,
                    'image_path': filepath,
                    'dialogue': panel.get('dialogue', ''),
                    'scene': panel.get('scene', '')
                })
        
        print(f"✓ All {len(panel_images)} panels generated!\n")
        return panel_images