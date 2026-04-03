"""Vision-Action Loop Agent.
This agent accepts an objective, captures a screenshot, queries a vision-capable LLM
for the next best action, parses the response, and (optionally) executes or simulates
the action via the Actuator. Includes a simple Critic loop for verification.
"""
from .vision import Vision
from .llm_client import LLMClient
from .actuator import Actuator
from .critic import Critic
import time
import re

class VisionAgent:
    def __init__(self):
        self.vision = Vision()
        self.llm = LLMClient()
        self.actuator = Actuator()

    def parse_commands(self, text: str):
        """Parses lines like [CMD: press "win"] or [CMD: click x y]
        Returns a list of dicts {type: 'press'|'click'|'wait'|'type', args: ...}
        """
        cmds = []
        for line in text.splitlines():
            line = line.strip()
            m = re.match(r"\[CMD:\s*(press|wait|type|click)\s*\"?(.*?)\"?\]", line, re.IGNORECASE)
            if not m:
                continue
            op = m.group(1).lower()
            arg = m.group(2).strip()
            if op == 'click':
                parts = arg.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    x = int(parts[0]); y = int(parts[1])
                    cmds.append({'type':'click','x':x,'y':y})
                else:
                    cmds.append({'type':'click'})
            elif op == 'press':
                cmds.append({'type':'press','key':arg})
            elif op == 'wait':
                cmds.append({'type':'wait'})
            elif op == 'type':
                cmds.append({'type':'type','text':arg})
        return cmds

    def run_task(self, objective: str, max_steps: int = 6, simulate: bool = True):
        """Run Vision-Action loop. When simulate=True, actuator actions are logged but not executed.
        Returns result string.
        """
        history = []
        system_prompt = open('prompts/action_prompt.txt','r',encoding='utf-8').read()

        for step in range(max_steps):
            # 1. Capture image and encode
            img_bytes = self.vision.capture_screen()
            img_b64 = self.vision.image_to_base64(img_bytes)

            # 2. Build user prompt
            user_prompt = f"TASK: {objective}\nHISTORY: {history[-3:]}\nProvide [THOUGHT] and [CMD:] lines."

            # 3. Query LLM (vision)
            resp = self.llm.generate_with_image(system_prompt, user_prompt, img_b64)
            history.append(resp)

            # 4. Parse commands
            cmds = self.parse_commands(resp)
            if not cmds:
                return f"No commands parsed at step {step+1}. LLM response: {resp}"

            # 5. Execute or simulate
            for c in cmds:
                if c['type'] == 'click':
                    if not simulate:
                        if 'x' in c and 'y' in c:
                            self.actuator.click(c['x'], c['y'])
                        else:
                            self.actuator.click()
                    else:
                        print(f"SIMULATE: click {c.get('x','')} {c.get('y','')}")
                elif c['type'] == 'press':
                    if not simulate:
                        self.actuator.press(c.get('key','enter'))
                    else:
                        print(f"SIMULATE: press {c.get('key','enter')}")
                elif c['type'] == 'wait':
                    time.sleep(1)
                elif c['type'] == 'type':
                    if not simulate:
                        self.actuator.press('')
                    else:
                        print(f"SIMULATE: type {c.get('text','')}")

            # 6. Critic verification example: if objective mentions spotify, verify active window
            if 'spotify' in objective.lower():
                ok = Critic.verify_window_contains('spotify', simulate=simulate)
                if ok:
                    return "Task appears successful (verified)."
                else:
                    # Inject failure message and retry
                    history.append('Critic: verification failed, retrying')
                    continue

            # Default success
            return "Task executed (simulated mode)."

        return "Max steps reached without success."
