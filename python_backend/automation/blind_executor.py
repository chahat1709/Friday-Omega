import pyautogui
import time
import subprocess

class BlindExecutor:
    """
    Executes tasks BLINDLY using OS shortcuts and commands.
    Used for high-speed performance on known tasks (Opening Apps, URLs).
    """
    def __init__(self):
        self.os_type = "windows"
        pyautogui.FAILSAFE = True

    def execute(self, instruction):
        """
        Parses natural language instruction into Blind Actions.
        """
        instruction = instruction.lower()
        print(f"[BlindExecutor] Executing: {instruction}")
        
        if "open" in instruction:
            # Extract target (e.g., "open chrome" -> "chrome")
            target = instruction.replace("open", "").strip()
            return self._open_app_or_url(target)
        
        if "minimize" in instruction or "desktop" in instruction:
            pyautogui.hotkey('win', 'd')
            return "Minimized all windows."
            
        # System shortcuts
        if "task manager" in instruction or "taskmgr" in instruction:
            return self._press_keys(['ctrl', 'shift', 'esc'])
        
        if "lock" in instruction or "lock screen" in instruction:
            return self._press_keys(['win', 'l'])
        
        if "shutdown" in instruction:
            return self._press_keys(['win', 'x', 'u', 'u'])
        
        if "restart" in instruction:
            return self._press_keys(['win', 'x', 'u', 'r'])
        
        if "sleep" in instruction:
            return self._press_keys(['win', 'x', 'u', 's'])
        
        # Volume controls
        if "volume up" in instruction or "louder" in instruction:
            for _ in range(5):  # Press 5 times
                self._press_keys(['volumeup'])
            return "Volume increased"
        
        if "volume down" in instruction or "quieter" in instruction:
            for _ in range(5):
                self._press_keys(['volumedown'])
            return "Volume decreased"
        
        if "mute" in instruction or "unmute" in instruction:
            return self._press_keys(['volumemute'])
        
        # Brightness (requires special keys, may not work on all PCs)
        if "brightness up" in instruction or "brighter" in instruction:
            return self._press_keys(['fn', 'f12'])  # Common on laptops
        
        if "brightness down" in instruction or "dimmer" in instruction:
            return self._press_keys(['fn', 'f11'])
        
        # Screenshot
        if "screenshot" in instruction or "print screen" in instruction:
            return self._press_keys(['printscreen'])
        
        if "snip" in instruction or "snipping" in instruction:
            return self._press_keys(['win', 'shift', 's'])
        
        # Window management  
        if "new desktop" in instruction or "virtual desktop" in instruction:
            return self._press_keys(['win', 'ctrl', 'd'])
        
        if "close desktop" in instruction:
            return self._press_keys(['win', 'ctrl', 'f4'])
        
        if "switch desktop" in instruction:
            return self._press_keys(['win', 'ctrl', 'right'])
        
        if "snap left" in instruction:
            return self._press_keys(['win', 'left'])
        
        if "snap right" in instruction:
            return self._press_keys(['win', 'right'])
        
        if "maximize" in instruction:
            return self._press_keys(['win', 'up'])
        
        if "minimize all" in instruction or "show desktop" in instruction:
            return self._press_keys(['win', 'd'])
        
        if "close window" in instruction or "alt f4" in instruction:
            return self._press_keys(['alt', 'f4'])
        
        # Clipboard
        if "clipboard history" in instruction:
            return self._press_keys(['win', 'v'])
        
        # Emoji picker
        if "emoji" in instruction:
            return self._press_keys(['win', '.'])
        
        # Application shortcuts
        if "calculator" in instruction:
            return self._run_command("calc")
        
        if "paint" in instruction:
            return self._run_command("mspaint")
        
        if "wordpad" in instruction:
            return self._run_command("write")
        
        if "command prompt" in instruction or "cmd" in instruction:
            return self._run_command("cmd")
        
        if "powershell" in instruction:
            return self._run_command("powershell")
        
        return "Unknown command. Try 'task manager', 'lock', 'volume up', 'screenshot', 'snap left', etc."

    def _open_app_or_url(self, target):
        """
        Smart Open: Tries to open as URL or App via Run Box.
        """
        # 1. Clean up target
        target = target.replace("app", "").replace("application", "").strip()
        
        # 2. Open Run Box
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5) # Wait for run box
        
        # 3. Determine command
        cmd = target
        if "chrome" in target: cmd = "chrome"
        elif "notepad" in target: cmd = "notepad"
        elif "calc" in target: cmd = "calc"
        elif "spotify" in target: cmd = "spotify"
        elif "whatsapp" in target: cmd = "whatsapp:" # Protocol handler
        elif "." in target: cmd = target # Likely a URL (gemini.google.com)
        else: cmd = target # Try generic name
        
        # 4. Type and Enter
        pyautogui.write(cmd)
        pyautogui.press('enter')
        
        return f"Opened '{cmd}' via Run Box."
