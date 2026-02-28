import random
import time
import os
from .vision_utils import VisionUtils
from .action_parser import ActionParser
from .executor import Executor

class HumanoidAgent:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.vision = VisionUtils()
        self.parser = ActionParser()
        self.executor = Executor()
        self.tts_enabled = False  # Set True when TTS engine is connected
        
        # Load System Prompt
        self.prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'vision_agent.md')
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            print(f"Error: Vision Prompt not found at {self.prompt_path}")
            self.system_prompt = "You are an agent."

    def solve_task(self, objective, max_steps=15):
        """
        Main Loop: See -> Think -> Act
        """
        print(f"Humanoid Agent: Starting Task - {objective}")
        history = []
        
        last_action = "None (Start of Task)"
        
        for step in range(max_steps):
            print(f"--- Step {step + 1}/{max_steps} ---")
            
            # 1. Capture State (Eyes)
            try:
                # Capture grid screenshot
                screenshot = self.vision.capture_screen_with_grid()
                # Encoded for VLM
                img_b64 = self.vision.image_to_base64(screenshot)
                # Debug save
                screenshot.save("latest_vision_debug.png")
            except Exception as e:
                print(f"Vision Capture Error: {e}")
                return "Error capturing screen."
            
            # 2. Construct Prompt (Cognition)
            # Format history for context
            history_text = "\n".join(history[-3:]) if history else "None"
            
            user_prompt = f"""USER OBJECTIVE: "{objective}"
PREVIOUS ACTION: {last_action}
HISTORY:
{history_text}

QUESTION: Verify if the PREVIOUS ACTION succeeded. Then determine the single next step. Output the command."""

            # 3. Get AI Decision (Brain)
            print("Analyzing screen with VLM...")
            try:
                response = self.llm.generate_with_image(self.system_prompt, user_prompt, img_b64)
            except AttributeError:
                return "LLM Engine does not support vision."
            except Exception as e:
                return f"LLM Error: {e}"

            print(f"AI Thought: {response}")
            
            # Extract "Thought" part for clean feedback if possible
            # Assuming standard Vision Agent Prompt format
            if "Thought:" in response:
                clean_thought = response.split("Thought:")[-1].split("Action:")[0].strip()
                print(f"\n[Humanoid Thinking] {clean_thought}...\n")
            
            # Cognitive Delay (Reaction Time)
            # Humans don't act instantly after seeing.
            reaction_time = random.uniform(1.0, 3.0) 
            time.sleep(reaction_time)
            
            # 4. Parse Actions
            actions = self.parser.parse_command(response)
            
            if not actions:
                print("No valid actions found. Retrying...")
                # Add failure to history to inform AI
                history.append(f"Step {step+1}: No action parsed from response '{response}'. Please output valid commands.")
                continue
                
            # 5. Execute Actions (Hands)
            step_results = []
            
            for action in actions:
                if action['type'] == 'done':
                    print("Humanoid Agent: Objective Verified as Complete.")
                    if self.tts_enabled:
                         # Placeholder for TTS - in a real integration this would call engine.speak
                         print("AI: Done sir. What would you like to do next?") 
                    return "Task Completed. Waiting for next command."
                
                result = self.executor.execute_action(action)
                step_results.append(result)
            
            # Update Last Action for next prompt
            if step_results:
                last_action = "; ".join(step_results)
                
            # Update History
            history.append(f"Step {step+1}: {', '.join(step_results)}")
                
            # 6. Wait for UI
            # Dynamic wait based on action type?
            # Basic wait
            time.sleep(1.5)
            
        return "Max steps reached without completion."

    def plan_mission(self, objective):
        """
        Start a complex mission. For now, maps directly to solve_task.
        Future: Break down into sub-tasks.
        """
        return self.solve_task(objective)
