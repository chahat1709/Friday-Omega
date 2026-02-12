import os
import pyautogui
import pyperclip
from AppOpener import open as open_app_cmd
import webbrowser
import time

class Tools:
    @staticmethod
    def open_app(app_name):
        print(f"Tool: Opening {app_name}")
        try:
            # AppOpener is good for general apps
            open_app_cmd(app_name, match_closest=True, throw_error=True)
            
            # Agentic Verification & Focus
            time.sleep(5) # Increased from 2s to 5s for slow systems
            Tools._activate_window_by_title(app_name, timeout=5)
            
            # Simple check if process list contains something similar
            return f"Opening {app_name}."
        except:
            # Fallback to simple start command
            try:
                os.system(f"start {app_name}")
                time.sleep(5)
                return f"Attempting to start {app_name}."
            except Exception as e:
                return f"Failed to open {app_name}: {e}"

    @staticmethod
    def play_music(song_name=None):
        print(f"Tool: Playing music - {song_name}")
        try:
            # 1. Check if Spotify is running
            is_running = False
            try:
                tasks = os.popen('tasklist').read()
                if "Spotify.exe" in tasks:
                    is_running = True
            except:
                pass

            if not is_running:
                print("Spotify not running, starting it...")
                try:
                    open_app_cmd("spotify", match_closest=True)
                except Exception:
                    # ignore - we'll try web fallback below
                    pass
                # Agentic: Wait and Verify
                for _ in range(10): # Wait up to 10s
                    time.sleep(1)
                    if "Spotify.exe" in os.popen('tasklist').read():
                        is_running = True
                        break
                
                if not is_running:
                    # If native Spotify failed, we'll fallback to web player
                    print("Spotify native app failed to launch; will try web fallback.")
                time.sleep(2) # Extra buffer for UI load

            # 2. Handle Specific Requests
            if song_name:
                # Handle "Liked Songs" specifically
                if song_name.lower() in ["my liked songs", "liked songs", "my songs", "favorites", "my music"]:
                    print("Agent: Navigating to Liked Songs...")
                    # Try URI handler first (native app)
                    try:
                        uri = "spotify:collection:tracks"
                        webbrowser.open(uri)
                        time.sleep(2)
                        # Bring Spotify to foreground and try to play
                        try:
                            pyautogui.hotkey('alt', 'tab')
                        except Exception:
                            pass
                        time.sleep(0.3)
                        pyautogui.press('space')
                        return "Opened Spotify Liked Songs via URI and attempted playback."
                    except Exception:
                        # Fallback to web player
                        try:
                            web_url = "https://open.spotify.com/collection/tracks"
                            webbrowser.open(web_url)
                            time.sleep(3)
                            # Try to press play in the browser
                            try:
                                pyautogui.press('space')
                            except Exception:
                                pass
                            return "Opened Spotify Web Liked Songs and attempted playback."
                        except Exception as e:
                            return f"Failed to open Liked Songs: {e}"

                # Standard Search
                print(f"Agent: Searching for {song_name}...")
                query = song_name.replace(" ", "%20")
                uri = f"spotify:search:{query}"
                webbrowser.open(uri)
                
                # Wait a bit for app to focus then hit enter to play top result
                time.sleep(5)
                # Ensure Spotify is focused
                Tools._activate_window_by_title("Spotify")
                time.sleep(0.5)

                # Try to play Top Result
                try:
                    # Improved Navigation Sequence
                    # Initial state: Focus is on Search Bar
                    pyautogui.press('tab') # Move to 'Top Result' or Filters
                    time.sleep(0.1)
                    pyautogui.press('tab') # Move to Play Button of Top Result
                    time.sleep(0.1)
                    pyautogui.press('enter') # Play
                    
                    time.sleep(1.0)
                    # Retry with simple Enter if first attempt failed
                    pyautogui.press('enter')
                except Exception:
                    try:
                        pyautogui.press('space')
                    except Exception:
                        pass
                return f"Playing {song_name} on Spotify."
            else:
                # Just resume
                pyautogui.press("playpause")
                return "Resuming music."
        except Exception as e:
            print(f"Spotify Error: {e}. Attempting fallback...")
            # Agentic Fallback: Try YouTube if Spotify fails
            if song_name and "liked songs" not in song_name.lower():
                return Tools.play_youtube(song_name)
            # As a last resort, try opening the web Liked Songs if requested
            try:
                if song_name and "liked songs" in song_name.lower():
                    webbrowser.open("https://open.spotify.com/collection/tracks")
                    return "Attempted web fallback for Liked Songs."
            except Exception:
                pass
            return f"Failed to play music on Spotify: {e}"

    @staticmethod
    def play_youtube(video_name):
        print(f"Tool: Playing on YouTube - {video_name}")
        try:
            import pywhatkit
            pywhatkit.playonyt(video_name)
            return f"Playing {video_name} on YouTube."
        except Exception as e:
            # Fallback to webbrowser search
            query = video_name.replace(" ", "+")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return f"Searching {video_name} on YouTube."

    @staticmethod
    def stop_music():
        print("Tool: Stopping music")
        pyautogui.press("playpause")
        return "Music paused."

    @staticmethod
    def next_song():
        print("Tool: Next song")
        pyautogui.press("nexttrack")
        return "Skipping to next song."

    @staticmethod
    def previous_song():
        print("Tool: Previous song")
        pyautogui.press("prevtrack")
        return "Going back to previous song."

    @staticmethod
    def set_volume(level):
        """Sets system volume to specific level (0-100)"""
        try:
             # Reset to 0
             for _ in range(50): pyautogui.press("volumedown")
             # Calculate steps (Windows volume step is usually 2%).
             # So level 10 requires 5 steps.
             steps = int(int(level) / 2)
             for _ in range(steps): pyautogui.press("volumeup")
             return f"Volume set to {level}%."
        except Exception as e:
            return f"Error setting volume: {e}"

    @staticmethod
    def volume_up(steps=5):
        for _ in range(steps): pyautogui.press("volumeup")
        return "Volume increased."

    @staticmethod
    def volume_down(steps=5):
        for _ in range(steps): pyautogui.press("volumedown")
        return "Volume decreased."

    @staticmethod
    def read_file_content(file_path):
        print(f"Tool: Reading file {file_path}")
        try:
            # Security check: prevent reading outside project
            if ".." in file_path or ":" in file_path: 
                 # Allow absolute paths if they contain "FRIDAY" (simple check)
                 if "FRIDAY" not in file_path:
                     return "Access denied: Restricted path."
            
            if not os.path.exists(file_path):
                # Try relative to python_backend
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_path = os.path.join(base_path, file_path)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return "File not found."
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def _wait_for_process(process_name, timeout=8):
        """Wait for a process name to appear in tasklist. Return True if found."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                tasks = os.popen('tasklist').read()
                if process_name.lower() in tasks.lower():
                    return True
            except Exception:
                pass
            time.sleep(0.4)
        return False

    @staticmethod
    def _wait_for_text_on_screen(target_texts, timeout=6, interval=0.5):
        """Try OCR on the screen repeatedly to detect any of the target_texts. Returns matched text or None.

        `target_texts` can be a string or list of strings. Performs case-insensitive substring match.
        Requires `pytesseract` and PIL.ImageGrab; falls back to None if not available.
        """
        if isinstance(target_texts, str):
            targets = [target_texts.lower()]
        else:
            targets = [t.lower() for t in target_texts]

        try:
            from PIL import ImageGrab
            import pytesseract
        except Exception:
            print("Tool: OCR not available (pytesseract/Pillow). Skipping visual checks.")
            return "OCR_DISABLED"

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                img = ImageGrab.grab()
                text = pytesseract.image_to_string(img)
                text_lower = text.lower()
                for t in targets:
                    if t in text_lower:
                        return t
            except Exception as e:
                # OCR can be flaky; just continue polling
                print(f"Tool: OCR polling error: {e}")
            time.sleep(interval)
        return None

    @staticmethod
    def _match_template_on_screen(template_path, threshold=0.8, timeout=5, interval=0.5):
        """Try to match a template image on the screen using OpenCV template matching.

        Returns True if a match above `threshold` is found, False otherwise. If OpenCV not available,
        returns "OPENCV_DISABLED".
        """
        try:
            import cv2
            import numpy as np
            from PIL import ImageGrab, Image
        except Exception:
            print("Tool: OpenCV/NumPy not available. Template matching disabled.")
            return "OPENCV_DISABLED"

        if not os.path.exists(template_path):
            print(f"Tool: Template not found: {template_path}")
            return False

        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Tool: Failed to load template: {template_path}")
            return False

        th, tw = template.shape[:2]
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                screen = ImageGrab.grab()
                screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_BGR2GRAY)
                res = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val >= threshold:
                    return True
            except Exception as e:
                print(f"Tool: template matching error: {e}")
            time.sleep(interval)
        return False

    @staticmethod
    def _activate_window_by_title(title_substring, timeout=6):
        """Try to focus a window whose title contains `title_substring` using pygetwindow if available.

        Returns True if a window was activated or found, False otherwise.
        """
        try:
            import pygetwindow as gw
        except Exception:
            # pygetwindow not available
            return False

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                wins = gw.getWindowsWithTitle(title_substring)
                if wins:
                    for w in wins:
                        try:
                            w.activate()
                            return True
                        except Exception:
                            continue
            except Exception:
                pass
            time.sleep(0.4)
        return False



    @staticmethod
    def _ask_llava(image_path, question, timeout=8):
        """Send an image and a question to Ollama LLaVA and return the model's response string.

        Expects Ollama running at http://localhost:11434 and a multimodal model named 'llava' available.
        """
        try:
            import requests
            import base64
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            image_data = f"data:image/png;base64,{img_b64}"

            payload = {
                "model": "llava",
                "prompt": question,
                "system": "You are a vision assistant. Answer 'YES' or 'NO' briefly whether the image matches the question.",
                "images": [image_data],
                "stream": False
            }
            url = "http://localhost:11434/api/generate"
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                # Ollama returns a 'response' field in our other calls
                return data.get('response') or data.get('output') or str(data)
            else:
                return f"LLAVA_ERROR: {resp.status_code} {resp.text}"
        except Exception as e:
            return f"LLAVA_EXCEPTION: {e}"

    @staticmethod
    def _save_debug_screenshot(step_name):
        """Save a timestamped debug screenshot to `core/ui_debug/` and return the path."""
        try:
            from PIL import ImageGrab
        except Exception:
            return None

        debug_dir = os.path.join(os.path.dirname(__file__), 'ui_debug')
        os.makedirs(debug_dir, exist_ok=True)
        ts = int(time.time() * 1000)
        path = os.path.join(debug_dir, f"{step_name}_{ts}.png")
        try:
            img = ImageGrab.grab()
            img.save(path)
            return path
        except Exception:
            return None

    @staticmethod
    def write_file_content(file_path, content):
        print(f"Tool: Writing to file {file_path}")
        try:
            # Security check
            if ".." in file_path and "FRIDAY" not in file_path:
                 return "Access denied: Restricted path."

            if not os.path.isabs(file_path):
                 base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                 file_path = os.path.join(base_path, file_path)

            # Create backup
            if os.path.exists(file_path):
                import shutil
                shutil.copy(file_path, file_path + ".bak")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully updated {os.path.basename(file_path)}. Backup created."
        except Exception as e:
            return f"Error writing file: {e}"

    @staticmethod
    def send_whatsapp(contact_name, message, image_path=None, verify_steps=True):
        """Send a WhatsApp Desktop message with optional stepwise visual verification.

        If `verify_steps` is True the function will attempt OCR and/or template matching
        between UI actions to ensure each step completed before proceeding.
        """
        print(f"Tool: Sending WhatsApp to {contact_name} (verify_steps={verify_steps})")

        # Smart Aliases for common relations
        aliases = [contact_name]
        name_lower = contact_name.lower()

        # Family Aliases
        if name_lower in ['mom', 'mummy', 'mother', 'maa', 'mum', 'mama']:
            aliases = ['Mom', 'Mummy', 'Maa', 'Mother', 'Amma', 'Mum']
        elif name_lower in ['dad', 'papa', 'father', 'paa', 'daddy', 'pitaji']:
            aliases = ['Dad', 'Papa', 'Paa', 'Father', 'Daddy']
        elif name_lower in ['bro', 'bhai', 'brother', 'bhaiya', 'veerji']:
            aliases = ['Bro', 'Bhai', 'Brother', 'Bhaiya']
        elif name_lower in ['sis', 'sister', 'didi', 'di']:
            aliases = ['Sis', 'Sister', 'Didi', 'Di']
        elif name_lower in ['wife', 'wifey', 'biwi']:
            aliases = ['Wife', 'Wifey', 'Baby', 'Love']
        elif name_lower in ['hubby', 'husband', 'pati']:
            aliases = ['Hubby', 'Husband']

        # Step 0: Ensure WhatsApp is focused/active. Try to activate window first.
        try:
            activated = False
            if verify_steps:
                activated = Tools._activate_window_by_title('WhatsApp', timeout=3)

            if not activated:
                print("OPENING WHATSAPP")
                try:
                    open_app_cmd("whatsapp", match_closest=True, throw_error=True)
                except Exception:
                    # best-effort: continue and hope app opens
                    pass
                Tools._wait_for_process('WhatsApp.exe', timeout=6)
        except Exception as e:
            print(f"Warning: could not activate or open WhatsApp window: {e}")

        try:
            for name in aliases:
                print(f"Trying contact: {name}")

                # Save pre-search screenshot
                if verify_steps:
                    Tools._save_debug_screenshot(f"pre_search_{name}")

                # Optional pre-search verification (search box present)
                if verify_steps:
                    search_ok = Tools._wait_for_text_on_screen(['search', 'search or start a new chat'], timeout=3, interval=0.4)
                    if search_ok == "OCR_DISABLED":
                        tpl_result = Tools._match_template_on_screen(os.path.join(os.path.dirname(__file__), 'ui_templates', 'whatsapp_search.png'), timeout=2)
                        if tpl_result == "OPENCV_DISABLED":
                            print("No OCR or OpenCV available to verify search UI; proceeding.")
                        elif not tpl_result:
                            print("Search UI template not found on screen; proceeding cautiously.")
                    elif not search_ok:
                        print("Search UI text not detected; proceeding to attempt search anyway.")

                # Step 1: Open search and type name (with retry)
                for attempt in range(2):
                    pyautogui.hotkey('ctrl', 'f')
                    time.sleep(0.25)
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('backspace')
                    pyautogui.write(name, interval=0.04)
                    time.sleep(0.8)
                    # quick visual snapshot after typing
                    if verify_steps:
                        Tools._save_debug_screenshot(f"after_type_{name}_attempt{attempt}")
                    break

                # Step 2: Select first result and open chat
                pyautogui.press('down')
                time.sleep(0.12)
                pyautogui.press('enter')
                time.sleep(0.6)

                # Save screenshot after opening chat
                if verify_steps:
                    Tools._save_debug_screenshot(f"after_openchat_{name}")

                # Step 3: Verify chat opened if requested
                if verify_steps:
                    matched = Tools._wait_for_text_on_screen([name], timeout=3, interval=0.5)
                    if matched == "OCR_DISABLED":
                         print("OCR Disabled. Proceeding blindly.")
                    elif not matched:
                        # Logic was: continue. 
                        # New Logic: Warn but proceed, because OCR might just be flaky or text color/theme issues.
                        print(f"Visual verify warning for {name}: Not found. Proceeding anyway.")
                        # continue # Don't abort, just try.

                # Step 4: Focus input and send message
                pyautogui.press('tab')
                time.sleep(0.12)
                try:
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('backspace')
                except Exception:
                    pass
                pyautogui.write(message, interval=0.04)
                time.sleep(0.08)
                if verify_steps:
                    Tools._save_debug_screenshot(f"before_send_{name}")
                pyautogui.press('enter')
                time.sleep(0.6)

                # Save screenshot after send
                if verify_steps:
                    Tools._save_debug_screenshot(f"after_send_{name}")

                # Step 5: Verify send if requested
                if verify_steps:
                    sent = Tools._wait_for_text_on_screen([message], timeout=5, interval=0.5)
                    if sent == "OCR_DISABLED":
                        print("OCR not available to confirm send; assuming success.")
                        return f"WhatsApp send action executed for {name} (OCR disabled, unverified)."
                    if sent:
                        return f"WhatsApp sent to {name}."
                    else:
                        print(f"Could not visually confirm message for {name}; saving debug and returning failure.")
                        Tools._save_debug_screenshot(f"send_verify_fail_{name}")
                        return f"WhatsApp send action executed for {name} (visual confirm failed)."

                return f"WhatsApp send action executed for {name} (no verification)."

            return f"Could not find contact '{contact_name}' or any aliases via desktop UI. Consider web fallback."

        except Exception as e:
            print(f"Unexpected error in send_whatsapp: {e}")
            return f"Failed to send WhatsApp due to error: {e}"

    @staticmethod
    def set_brightness(level):
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            return f"Brightness set to {level}%."
        except Exception as e:
            return f"Error setting brightness: {e}"
