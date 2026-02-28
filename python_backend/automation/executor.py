import pyautogui
import time
import random
import math
from .vision_utils import VisionUtils

class Executor:
    def __init__(self):
        self.vision = VisionUtils()
        pyautogui.FAILSAFE = True # Move mouse to corner to abort
        
    def _human_move(self, target_x, target_y, duration=None):
        """
        Simulates natural human mouse movement with:
        1. Fitts's Law acceleration (start slow, fast middle, stop slow)
        2. Arc/Curvature (never straight lines)
        3. Overshoot (missing the target slightly and correcting)
        4. Micro-jitter (tremors)
        """
        start_x, start_y = pyautogui.position()
        dist = math.hypot(target_x - start_x, target_y - start_y)
        
        # 1. Dynamic Duration based on Fitts's Law (Distance + randomness)
        if duration is None:
            # Base speed: fast for short, slower for long (but capped)
            base_time = random.uniform(0.3, 0.6) + (dist / 2000.0) 
            duration = min(1.5, base_time)

        # 2. Path Generation (Cubic Bezier)
        # Random control points for arc
        offset = dist * 0.2
        ctrl1_x = start_x + (target_x - start_x) * 0.2 + random.uniform(-offset, offset)
        ctrl1_y = start_y + (target_y - start_y) * 0.2 + random.uniform(-offset, offset)
        ctrl2_x = start_x + (target_x - start_x) * 0.8 + random.uniform(-offset, offset)
        ctrl2_y = start_y + (target_y - start_y) * 0.8 + random.uniform(-offset, offset)

        # 3. Overshoot Handling
        # Occasional overshoot (70% chance)
        final_x, final_y = target_x, target_y
        did_overshoot = False
        if random.random() < 0.7:
             overshoot_dist = min(30, dist * 0.05) # Max 30px overshoot
             angle = math.atan2(target_y - start_y, target_x - start_x)
             final_x += math.cos(angle) * overshoot_dist
             final_y += math.sin(angle) * overshoot_dist
             did_overshoot = True

        # Execute Movement
        steps = max(25, int(duration * 60))
        for i in range(steps):
            t = i / steps
            # Smooth step (Ease-in-out)
            t_smooth = t * t * (3 - 2 * t)
            
            bx = (1-t_smooth)**3*start_x + 3*(1-t_smooth)**2*t_smooth*ctrl1_x + 3*(1-t_smooth)*t_smooth**2*ctrl2_x + t_smooth**3*final_x
            by = (1-t_smooth)**3*start_y + 3*(1-t_smooth)**2*t_smooth*ctrl1_y + 3*(1-t_smooth)*t_smooth**2*ctrl2_y + t_smooth**3*final_y
            
            # 4. Micro-jitter
            jitter_x = random.uniform(-1, 1)
            jitter_y = random.uniform(-1, 1)
            
            pyautogui.moveTo(bx + jitter_x, by + jitter_y)
            
            # Variable sleep to simulate processor/nerve interrupt (tiny)
            time.sleep(duration / steps)
            
        # Correction Step if Overshot
        if did_overshoot:
            # Snap back to actual target slowly like a correction
            correction_duration = random.uniform(0.1, 0.2)
            c_steps = 10
            curr_x, curr_y = pyautogui.position()
            for i in range(c_steps):
                t = i / c_steps
                # Linear correction is fine for short distance
                nx = curr_x + (target_x - curr_x) * t
                ny = curr_y + (target_y - curr_y) * t
                pyautogui.moveTo(nx, ny)
                time.sleep(correction_duration / c_steps)
                
        pyautogui.moveTo(target_x, target_y) # Hard ensure

    def execute_action(self, action):
        print(f"Executing Action: {action}")
        
        if action['type'] == 'click':
            grid_id = action['target']
            coords = self.vision.get_coordinates_from_grid(grid_id)
            if coords:
                x, y = coords
                # Huma-like movement (calculated internally)
                self._human_move(x, y)
                
                pyautogui.click()
                return f"Clicked at {grid_id} ({x}, {y})"
            else:
                return f"Invalid Grid ID: {grid_id}"

        elif action['type'] == 'double_click':
            grid_id = action['target']
            coords = self.vision.get_coordinates_from_grid(grid_id)
            if coords:
                x, y = coords
                self._human_move(x, y)
                pyautogui.doubleClick()
                return f"Double Clicked at {grid_id}"
            return f"Invalid Grid ID: {grid_id}"

        elif action['type'] == 'right_click':
            grid_id = action['target']
            coords = self.vision.get_coordinates_from_grid(grid_id)
            if coords:
                x, y = coords
                self._human_move(x, y)
                pyautogui.rightClick()
                return f"Right Clicked at {grid_id}"
            return f"Invalid Grid ID: {grid_id}"
                
        elif action['type'] == 'type':
            text = action['content']
            pyautogui.write(text, interval=random.uniform(0.05, 0.15)) # Variable typing speed
            return f"Typed: {text}"
            
        elif action['type'] == 'press':
            keys = action['key'].lower().split('+')
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
                return f"Pressed combo: {'+'.join(keys)}"
            else:
                pyautogui.press(keys[0])
                return f"Pressed key: {keys[0]}"
        
        elif action['type'] == 'wait':
            secs = action.get('seconds', 1)
            time.sleep(secs)
            return f"Waited {secs}s"
            
        elif action['type'] == 'done':
            return "Task Completed."
            
        return "Unknown Action"

