import re

class ActionParser:
    @staticmethod
    def parse_command(llm_response):
        """
        Extracts commands like [CLICK: A1], [TYPE: "text"], [PRESS: key]
        Returns a list of actions: [{'type': 'click', 'target': 'A1'}, ...]
        """
        actions = []
        
        # Regex patterns
        # Supports CLICK, DOUBLE_CLICK, RIGHT_CLICK
        click_pattern = r'\[(CLICK|DOUBLE_CLICK|RIGHT_CLICK):\s*([A-J](?:10|[1-9]))\]'
        type_pattern = r'\[TYPE:\s*"(.*?)"\]'
        press_pattern = r'\[PRESS:\s*([\w\s]+)\]' # Allow spaces in key names if needed
        wait_pattern = r'\[WAIT:\s*(\d+)\]'
        done_pattern = r'\[DONE\]'
        
        # Find all matches
        # Note: We should preserve order if possible, but finding all types separately mocks that up.
        # Better approach: Iterate through the string finding any tags.
        
        tag_pattern = r'\[(CLICK|DOUBLE_CLICK|RIGHT_CLICK|TYPE|PRESS|WAIT|DONE)(?::\s*([^\]]+))?\]'
        matches = re.findall(tag_pattern, llm_response, re.IGNORECASE)
        
        for cmd_type, content in matches:
            cmd_type = cmd_type.upper()
            content = content.strip() if content else ""
            
            if cmd_type == 'CLICK':
                actions.append({'type': 'click', 'target': content})
            elif cmd_type == 'DOUBLE_CLICK':
                actions.append({'type': 'double_click', 'target': content})
            elif cmd_type == 'RIGHT_CLICK':
                actions.append({'type': 'right_click', 'target': content})
            elif cmd_type == 'TYPE':
                # Remove quotes if regex captured them (the simplified regex above captures the whole content)
                # Let's fix content: regex above is greedy [Tag: content].
                # User prompt says [TYPE: "text"]. Content will be `"text"`.
                clean_text = content.strip('"')
                actions.append({'type': 'type', 'content': clean_text})
            elif cmd_type == 'PRESS':
                 actions.append({'type': 'press', 'key': content})
            elif cmd_type == 'WAIT':
                 try:
                     secs = int(content)
                 except: 
                     secs = 1
                 actions.append({'type': 'wait', 'seconds': secs})
            elif cmd_type == 'DONE':
                actions.append({'type': 'done'})

        return actions
