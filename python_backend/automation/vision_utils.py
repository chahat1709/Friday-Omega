from PIL import Image, ImageDraw, ImageFont
import pyautogui
import io
import base64

import os

class VisionUtils:
    def __init__(self):
        self.rows = 10
        self.cols = 10
        self.screen_width, self.screen_height = pyautogui.size()
        
    def capture_screen_with_grid(self):
        # Capture screenshot
        screenshot = pyautogui.screenshot()
        
        # Create drawing object
        draw = ImageDraw.Draw(screenshot)
        
        # Calculate grid sizes
        cell_w = self.screen_width / self.cols
        cell_h = self.screen_height / self.rows
        
        # Draw Grid
        for i in range(1, self.cols):
            x = i * cell_w
            draw.line([(x, 0), (x, self.screen_height)], fill="red", width=2)
            
        for i in range(1, self.rows):
            y = i * cell_h
            draw.line([(0, y), (self.screen_width, y)], fill="red", width=2)
            
        # Draw Labels (A1, A2... J10)
        # Using default font for simplicity, can load TTF if needed
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        row_labels = "ABCDEFGHIJ"
        for r in range(self.rows):
            for c in range(self.cols):
                label = f"{row_labels[r]}{c+1}"
                x = (c * cell_w) + 10
                y = (r * cell_h) + 10
                # Draw text with background for visibility
                bbox = draw.textbbox((x, y), label, font=font)
                draw.rectangle(bbox, fill="black")
                draw.text((x, y), label, fill="white", font=font)
                
        # DEBUG: Save to disk to verify vision
        debug_path = os.path.join(os.getcwd(), "debug_active_view.png")
        screenshot.save(debug_path)
        print(f"DEBUG: Saved vision capture to {debug_path}")

        return screenshot

    def image_to_base64(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def get_coordinates_from_grid(self, grid_id):
        # grid_id example: "A1", "J10"
        if not grid_id or len(grid_id) < 2:
            return None
            
        row_char = grid_id[0].upper()
        col_str = grid_id[1:]
        
        if row_char not in "ABCDEFGHIJ":
            return None
        
        try:
            col_num = int(col_str)
            if col_num < 1 or col_num > 10:
                return None
        except:
            return None
            
        row_idx = "ABCDEFGHIJ".index(row_char)
        col_idx = col_num - 1
        
        cell_w = self.screen_width / self.cols
        cell_h = self.screen_height / self.rows
        
        # Calculate center of the cell
        center_x = (col_idx * cell_w) + (cell_w / 2)
        center_y = (row_idx * cell_h) + (cell_h / 2)
        
        return int(center_x), int(center_y)
