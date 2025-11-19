import os
import requests
from pathlib import Path
from PIL import Image
import io
import time

class ComicImageGenerator:
    def __init__(self):
        print("✓ Using Pollinations.ai for image generation (free + no token required)")

        self.style = (
            "comic book illustration, professional comic art, clear lines, vibrant colors, "
            "graphic novel style, detailed, high quality, realistic shading"
        )

    # -------------------------------
    #  FREE IMAGE GENERATOR (MAIN)
    # -------------------------------
    def generate_with_pollinations(self, prompt):
        """Generate an image using Pollinations.ai (free endpoint)."""
        try:
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"

            response = requests.get(url, timeout=60)
            img = Image.open(io.BytesIO(response.content))
            return img

        except Exception as e:
            print(f"Pollinations error: {e}")
            raise

    # ----------------------------------------------
    #   PANEL GENERATION (NOW USING POLLINATIONS)
    # ----------------------------------------------
    def generate_panel_image(self, panel, character_descriptions, panel_number, output_dir='static/comics'):
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        scene = panel.get('scene', '')
        characters = panel.get('characters', [])

        # Character descriptions
        char_details = ""
        if characters and character_descriptions:
            for char in characters[:2]:
                if char in character_descriptions:
                    desc = character_descriptions[char][:120]
                    char_details += f"{char}: {desc}. "

        # Build the prompt
        prompt = (
            f"{self.style}. "
            f"{char_details} "
            f"Scene showing: {scene[:200]}. "
            "NOT anime, NOT manga. Realistic Western comic style. One single panel."
        )

        filename = f"panel_{panel_number}.png"
        filepath = os.path.join(output_dir, filename)

        print(f"\n🎨 Generating panel {panel_number}...")
        print(f"   Scene: {scene[:70]}...")

        # Try Pollinations first
        try:
            image = self.generate_with_pollinations(prompt)
            image.save(filepath)
            print(f"   ✓ Panel {panel_number} generated using Pollinations.ai")
            return filepath

        except Exception as e:
            print(f"   ✗ Pollinations failed: {e}")

        # Fallback: placeholder
        print(f"   ⚠ Creating placeholder for panel {panel_number}")
        self.create_placeholder(panel_number, scene, filepath)
        return filepath

    # ----------------------------------------------
    #    SIMPLE PLACEHOLDER IF EVERYTHING FAILS
    # ----------------------------------------------
    def create_placeholder(self, panel_number, scene, filepath):
        img = Image.new("RGB", (1024, 1024), (240, 240, 240))
        d = Image.fromarray(img)

        img.save(filepath)
        print(f"   ✓ Placeholder saved for panel {panel_number}")

    # ----------------------------------------------
    #   GENERATE ALL PANELS
    # ----------------------------------------------
    def generate_all_panels(self, script, character_descriptions, comic_id):
        output_dir = f"static/comics/{comic_id}"
        panel_images = []

        panels = script.get("panels", [])
        print(f"\n🎬 Generating {len(panels)} comic panels...\n")

        for i, panel in enumerate(panels):
            panel_number = panel.get("panel_number", i + 1)

            # Small pause to avoid spam
            time.sleep(1)

            filepath = self.generate_panel_image(
                panel,
                character_descriptions,
                panel_number,
                output_dir
            )

            panel_images.append({
                "panel_number": panel_number,
                "image_path": filepath,
                "dialogue": panel.get("dialogue", ""),
                "scene": panel.get("scene", "")
            })

        print(f"\n✓ All {len(panel_images)} panels generated!\n")
        return panel_images
