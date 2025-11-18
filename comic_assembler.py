from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class ComicAssembler:
    def __init__(self):
        self.panel_width = 512
        self.panel_height = 512
        self.border_width = 5
        self.padding = 10
        
    def add_text_to_panel(self, image, text, position='bottom'):
        """Add dialogue text in a proper comic speech bubble"""
        draw = ImageDraw.Draw(image)
        
        # Try to use a nice comic font
        try:
            font = ImageFont.truetype("arialbd.ttf", 24)  # Bold for comic style
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        img_width, img_height = image.size
        
        # Wrap text
        wrapper = textwrap.TextWrapper(width=35)
        wrapped_text = wrapper.fill(text=text)
        
        # Calculate text dimensions
        lines = wrapped_text.split('\n')
        line_height = 35
        total_text_height = len(lines) * line_height
        
        # Speech bubble dimensions
        bubble_padding = 25
        bubble_width = img_width - 80
        bubble_height = total_text_height + 2 * bubble_padding
        
        # Position bubble
        if position == 'bottom':
            bubble_x = 40
            bubble_y = img_height - bubble_height - 40
        else:
            bubble_x = 40
            bubble_y = 40
        
        # Draw speech bubble (white with black border)
        bubble_coords = [
            bubble_x, bubble_y,
            bubble_x + bubble_width, bubble_y + bubble_height
        ]
        
        # Draw shadow for depth
        shadow_offset = 5
        draw.ellipse(
            [c + shadow_offset for c in bubble_coords],
            fill='#CCCCCC'
        )
        
        # Draw main bubble
        draw.ellipse(bubble_coords, fill='white', outline='black', width=4)
        
        # Draw speech bubble tail (triangle pointing to speaker)
        if position == 'bottom':
            tail_points = [
                (bubble_x + 60, bubble_y + bubble_height),
                (bubble_x + 40, bubble_y + bubble_height + 20),
                (bubble_x + 80, bubble_y + bubble_height)
            ]
        else:
            tail_points = [
                (bubble_x + 60, bubble_y),
                (bubble_x + 40, bubble_y - 20),
                (bubble_x + 80, bubble_y)
            ]
        
        draw.polygon(tail_points, fill='white', outline='black')
        
        # Draw text inside bubble
        text_y = bubble_y + bubble_padding
        for line in lines:
            # Center each line
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = bubble_x + (bubble_width - text_width) // 2
            
            draw.text((text_x, text_y), line, fill='black', font=font)
            text_y += line_height
        
        return image
    
    def create_panel_with_border(self, image_path, dialogue):
        """Create a panel with border and dialogue"""
        try:
            # Open and resize image
            img = Image.open(image_path)
            img = img.resize((self.panel_width, self.panel_height))
            
            # Add dialogue if present
            if dialogue:
                img = self.add_text_to_panel(img, dialogue)
            
            # Create image with border
            bordered_width = self.panel_width + 2 * self.border_width
            bordered_height = self.panel_height + 2 * self.border_width
            
            bordered_img = Image.new('RGB', (bordered_width, bordered_height), 'black')
            bordered_img.paste(img, (self.border_width, self.border_width))
            
            return bordered_img
            
        except Exception as e:
            print(f"Error creating panel: {e}")
            return None
    
    def assemble_comic(self, panel_images, output_path, title="", layout='2x2'):
        """Assemble all panels into a single comic image"""
        
        if not panel_images:
            print("No panel images to assemble")
            return None
        
        # Sort panels by panel number
        panel_images = sorted(panel_images, key=lambda x: x['panel_number'])
        
        # Determine grid layout
        if layout == '2x2' or len(panel_images) == 4:
            cols, rows = 2, 2
        elif layout == '1x4' or len(panel_images) <= 4:
            cols, rows = 1, len(panel_images)
        else:
            cols = 2
            rows = (len(panel_images) + 1) // 2
        
        # Create bordered panels
        bordered_panels = []
        for panel in panel_images:
            bordered = self.create_panel_with_border(
                panel['image_path'],
                panel.get('dialogue', '')
            )
            if bordered:
                bordered_panels.append(bordered)
        
        if not bordered_panels:
            return None
        
        # Calculate final comic dimensions
        panel_full_width = self.panel_width + 2 * self.border_width
        panel_full_height = self.panel_height + 2 * self.border_width
        
        title_height = 80 if title else 0
        
        comic_width = cols * panel_full_width + (cols + 1) * self.padding
        comic_height = rows * panel_full_height + (rows + 1) * self.padding + title_height
        
        # Create final comic image
        comic = Image.new('RGB', (comic_width, comic_height), 'white')
        draw = ImageDraw.Draw(comic)
        
        # Add title
        if title:
            try:
                title_font = ImageFont.truetype("arial.ttf", 36)
            except:
                title_font = ImageFont.load_default()
            
            # Center the title
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (comic_width - title_width) // 2
            
            draw.text((title_x, 20), title, fill='black', font=title_font)
        
        # Paste panels into grid
        for idx, panel in enumerate(bordered_panels):
            row = idx // cols
            col = idx % cols
            
            x = col * panel_full_width + (col + 1) * self.padding
            y = row * panel_full_height + (row + 1) * self.padding + title_height
            
            comic.paste(panel, (x, y))
        
        # Save the final comic
        try:
            comic.save(output_path)
            print(f"Comic saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving comic: {e}")
            return None