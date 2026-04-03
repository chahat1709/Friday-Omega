"""Critic: verifies results of actions and requests retries when needed.
For now, provides a simple active-window title check using pygetwindow.
"""
try:
    import pygetwindow as gw
except Exception:
    gw = None

class Critic:
    @staticmethod
    def verify_window_contains(keyword: str, simulate: bool = True) -> bool:
        """Return True if the active window title contains keyword. In simulate mode, return True.
        """
        if simulate:
            return True
        if not gw:
            return False
        try:
            win = gw.getActiveWindow()
            if not win:
                return False
            title = win.title.lower()
            return keyword.lower() in title
        except Exception:
            return False
