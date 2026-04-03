"""Actuator wrappers around pyautogui and other OS controls.
Keep calls in one place so the ActionEngine can be simpler and testable.
"""
import pyautogui
import time

class Actuator:
    @staticmethod
    def click(x:int=None, y:int=None):
        if x is None or y is None:
            pyautogui.click()
        else:
            pyautogui.click(x, y)
        time.sleep(0.2)

    @staticmethod
    def press(key:str):
        pyautogui.press(key)
        time.sleep(0.1)
