from .vision_utils import VisionUtils
from .action_parser import ActionParser
from .executor import Executor
from .humanoid_agent import HumanoidAgent

class AgentLoop:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.vision = VisionUtils()
        self.parser = ActionParser()
        self.executor = Executor()
        
        # Load System Prompt
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'vision_agent.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()

    def run_task(self, objective, max_steps=10):
        print(f"Starting Autonomous Task: {objective}")
        history = []
        
        for step in range(max_steps):
            print(f"--- Step {step + 1} ---")
            
            # 1. Capture State (Eyes)
            screenshot = self.vision.capture_screen_with_grid()
            img_b64 = self.vision.image_to_base64(screenshot)
            
            # 2. Construct Prompt (Cognition)
            user_prompt = f"""USER OBJECTIVE: "{objective}"
CURRENT HISTORY: {history[-2:] if history else "None"}

IMAGE: <image_base64_placeholder> (The AI sees the grid image here)

QUESTION: Look at the grid. What is the single next step to move closer to the objective?"""

            # Note: Since we can't easily inject base64 into the text prompt for standard LLMs without a vision adapter,
            # we assume the LLM Engine supports vision or we use a multimodal endpoint.
            # For this implementation, we will assume the LLM class handles the image if passed.
            # If using Ollama LLaVA, we need to pass the image separately.
            
            # 3. Get AI Decision
            # We need to modify LLMEngine to accept images or use a specific method here.
            # For now, we'll simulate the call structure.
            
            # IMPORTANT: This requires the underlying LLM to support vision (like LLaVA).
            # If using Qwen-Coder (text-only), this won't work for vision.
            # We need to switch to LLaVA for this loop.
            
            print("Analyzing screen...")
            # This is a placeholder for the actual LLaVA call
            # response = self.llm.generate_vision(self.system_prompt, user_prompt, img_b64)
            
            # Since we don't have the LLaVA method in LLMEngine yet, we'll stub it or fail gracefully.
            # To make this work, LLMEngine needs a 'generate_with_image' method.
            
            # For now, let's assume we have it.
            try:
                response = self.llm.generate_with_image(self.system_prompt, user_prompt, img_b64)
            except AttributeError:
                print("Error: LLMEngine does not support vision (generate_with_image).")
                return "Vision Model not available."

            print(f"AI Thought: {response}")
            
            # 4. Parse Actions
            actions = self.parser.parse_command(response)
            
            if not actions:
                print("No valid actions found. Retrying...")
                continue
                
            # 5. Execute Actions (Hands)
            for action in actions:
                if action['type'] == 'done':
                    print("Task Completed by AI.")
                    return "Task Completed."
                
                result = self.executor.execute_action(action)
                history.append(f"Step {step+1}: {result}")
                
            # 6. Wait for UI
            time.sleep(2)
            
        return "Max steps reached."
