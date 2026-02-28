import subprocess
import time
import re
import urllib.parse

class MobileAgent:
    """
    Controls Android devices using ADB (Android Debug Bridge).
    Requires 'adb' to be in the system PATH or provided.
    """
    def __init__(self, adb_path="adb"):
        self.adb_path = adb_path
        self.device_id = None
        self.screen_width = 1080  # Default, will be detected
        self.screen_height = 1920
        self.check_connection()

    def check_connection(self):
        """Checks for connected devices and detects screen size."""
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
            devices = result.stdout.strip().split('\n')[1:]
            valid_devices = [line.split('\t')[0] for line in devices if 'device' in line]
            
            if valid_devices:
                self.device_id = valid_devices[0]
                self._detect_screen_size()
                print(f"[MobileAgent] Connected to {self.device_id} ({self.screen_width}x{self.screen_height})")
                return True
            else:
                print("[MobileAgent] No device found. Please connect via USB/WiFi.")
                return False
        except FileNotFoundError:
            print("[MobileAgent] ADB not found in PATH.")
            return False
        except Exception as e:
            print(f"[MobileAgent] Connection error: {e}")
            return False
    
    def _detect_screen_size(self):
        """Detect actual screen size of connected device."""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_id, "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Output like: "Physical size: 1080x1920"
            match = re.search(r'(\d+)x(\d+)', result.stdout)
            if match:
                self.screen_width = int(match.group(1))
                self.screen_height = int(match.group(2))
        except:
            pass  # Keep defaults

    def execute(self, instruction):
        """
        Parses high-level instructions into ADB commands.
        Current support: 'open [app]', 'tap', 'swipe', 'home', 'back'.
        """
        if not self.device_id and not self.check_connection():
            return "Error: No mobile device connected."

        instruction = instruction.lower()
        print(f"[MobileAgent] Executing: {instruction}")

        if "open" in instruction:
            valid_app = self._extract_app_package(instruction)
            if valid_app:
                return self._adb_shell(f"monkey -p {valid_app} -c android.intent.category.LAUNCHER 1")
            else:
                return "Unknown App. Try 'open youtube' or 'open settings'."

        if "tap" in instruction or "click" in instruction:
            # TODO: Add vision-based coordinate mapping.
            # For now, blindly tapping center? No, this requires coordinates.
            # Only support specific blind taps if coordinates provided, else fails.
            return "Tap requires coordinates (Visual Loop). Request Vision Agent."

        if "home" in instruction:
            return self._adb_input("keyevent 3")
            
        if "back" in instruction:
            return self._adb_input("keyevent 4")
            
        if "swipe" in instruction:
            # Dynamic swipe based on screen size
            center_x = self.screen_width // 2
            start_y = int(self.screen_height * 0.75)  # Bottom 3/4
            end_y = int(self.screen_height * 0.25)    # Top 1/4
            return self._adb_input(f"swipe {center_x} {start_y} {center_x} {end_y} 300")
            
        if "type" in instruction or "send" in instruction:
             # Extract text (fix encoding bug)
             text = instruction.split("type")[-1].strip() if "type" in instruction else instruction.split("send")[-1].strip()
             # Properly URL encode spaces and special chars
             safe_text = urllib.parse.quote(text, safe='')
             return self._adb_input(f"text '{safe_text}'")

        return "Unknown Mobile Command."

    def _extract_app_package(self, instruction):
        """Map app names to package names (expanded list)."""
        # Common apps
        if "chrome" in instruction: return "com.android.chrome"
        if "youtube" in instruction: return "com.google.android.youtube"
        if "settings" in instruction: return "com.android.settings"
        if "spotify" in instruction: return "com.spotify.music"
        if "whatsapp" in instruction: return "com.whatsapp"
        if "instagram" in instruction: return "com.instagram.android"
        if "facebook" in instruction: return "com.facebook.katana"
        if "twitter" in instruction or "x" in instruction: return "com.twitter.android"
        if "gmail" in instruction: return "com.google.android.gm"
        if "maps" in instruction: return "com.google.android.apps.maps"
        if "photos" in instruction: return "com.google.android.apps.photos"
        if "play store" in instruction: return "com.android.vending"
        if "calculator" in instruction: return "com.android.calculator2"
        if "calendar" in instruction: return "com.android.calendar"
        if "camera" in instruction: return "com.android.camera2"
        if "clock" in instruction: return "com.android.deskclock"
        if "contacts" in instruction: return "com.android.contacts"
        if "files" in instruction: return "com.android.documentsui"
        if "phone" in instruction or "dialer" in instruction: return "com.android.dialer"
        if "messages" in instruction or "sms" in instruction: return "com.android.mms"
        if "telegram" in instruction: return "org.telegram.messenger"
        if "tiktok" in instruction: return "com.zhiliaoapp.musically"
        if "netflix" in instruction: return "com.netflix.mediaclient"
        if "amazon" in instruction: return "com.amazon.mShop.android.shopping"
        if "uber" in instruction: return "com.ubercab"
        return None

    def _adb_input(self, command):
        return self._adb_shell(f"input {command}")

    def _adb_shell(self, command):
        """Execute ADB shell command with error handling."""
        if not self.device_id:
            if not self.check_connection():
                return "Error: Device not connected"
        
        try:
            cmd = [self.adb_path, "-s", self.device_id, "shell"] + command.split()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
            return f"Executed ADB: {command}"
        except subprocess.TimeoutExpired:
            return f"ADB Error: Command timeout"
        except subprocess.CalledProcessError as e:
            return f"ADB Error: {e.stderr if e.stderr else str(e)}"
        except Exception as e:
            return f"ADB Error: {str(e)}"
