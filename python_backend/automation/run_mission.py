import sys
import os
import argparse

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.llm import LLMEngine
from automation.humanoid_agent import HumanoidAgent

def run_mission(objective):
    print(f"Initializing Agent for Mission: {objective}")
    
    # Initialize LLM (Ensure path is correct or ignored by Ollama wrapper)
    llm = LLMEngine("python_backend/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf", n_ctx=2048)
    
    # Initialize Humanoid
    agent = HumanoidAgent(llm)
    
    print("--- STARTING MISSION ---")
    print("PLEASE ENSURE OLLAMA IS RUNNING (ollama run llava)")
    print("Switching control to Agent in 3 seconds...")
    import time
    time.sleep(3)
    
    result = agent.solve_task(objective, max_steps=20)
    print(f"Mission Result: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("objective", type=str, help="The mission objective")
    args = parser.parse_args()
    
    run_mission(args.objective)
