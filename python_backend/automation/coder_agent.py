import os
import re

class CoderAgent:
    """
    AI-powered code generation and editing agent.
    Uses LLM to write, modify, and debug code.
    """
    
    def __init__(self, llm_engine):
        self.llm = llm_engine
        self.code_context = {}
    
    def execute(self, instruction):
        """
        Parse coding instructions and generate/edit code.
        """
        instruction_lower = instruction.lower()
        print(f"[Coder] Executing: {instruction}")
        
        # Code generation
        if "write" in instruction_lower or "create" in instruction_lower:
            return self._generate_code(instruction)
        
        # Code explanation
        if "explain" in instruction_lower or "what does" in instruction_lower:
            return self._explain_code(instruction)
        
        # Code debugging
        if "debug" in instruction_lower or "fix" in instruction_lower:
            return self._debug_code(instruction)
        
        # Code refactoring
        if "refactor" in instruction_lower or "improve" in instruction_lower:
            return self._refactor_code(instruction)
        
        return "Unknown coding task. Try: 'write a function to...', 'explain this code', 'debug this error'"
    
    def _generate_code(self, instruction):
        """
        Generate new code based on natural language description.
        """
        # Extract programming language if specified
        language = self._detect_language(instruction)
        
        prompt = f"""Generate {language} code for the following task:
{instruction}

Requirements:
- Write clean, well-commented code
- Include error handling
- Follow best practices
- Provide a brief explanation of your approach

Output format:
```{language}
[code here]
```

Explanation: [brief explanation]
"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are an expert programmer. Write production-ready code.",
                temperature=0.7
            )
            
            # Extract code from response
            code = self._extract_code_block(response)
            
            # Store in context for potential follow-up
            self.code_context['last_generated'] = code
            
            return f"[Coder] Generated Code:\n\n{response}"
            
        except Exception as e:
            return f"[Coder] Error generating code: {e}"
    
    def _explain_code(self, instruction):
        """
        Explain how code works.
        """
        # Extract code snippet from instruction or use last generated
        code = self._extract_code_from_instruction(instruction)
        
        if not code:
            code = self.code_context.get('last_generated', '')
        
        if not code:
            return "Please provide the code you want explained."
        
        prompt = f"""Explain the following code in detail:

```
{code}
```

Provide:
1. Overall purpose
2. Step-by-step breakdown
3. Key concepts used
4. Potential improvements
"""
        
        try:
            explanation = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a patient programming instructor.",
                temperature=0.5
            )
            return f"[Coder] Code Explanation:\n\n{explanation}"
        except:
            return "Error explaining code"
    
    def _debug_code(self, instruction):
        """
        Debug code and suggest fixes.
        """
        code = self._extract_code_from_instruction(instruction)
        error_msg = self._extract_error_message(instruction)
        
        prompt = f"""Debug the following code:

```
{code}
```

Error message:
{error_msg}

Provide:
1. Explanation of the error
2. Fixed code
3. Prevention tips
"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are an expert debugger.",
                temperature=0.3
            )
            return f"[Coder] Debug Analysis:\n\n{response}"
        except:
            return "Error debugging code"
    
    def _refactor_code(self, instruction):
        """
        Refactor code for better quality.
        """
        code = self._extract_code_from_instruction(instruction)
        
        prompt = f"""Refactor the following code to improve:
- Readability
- Performance
- Maintainability
- Best practices

Original code:
```
{code}
```

Provide refactored code with explanations of changes.
"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a senior software engineer focused on code quality.",
                temperature=0.5
            )
            return f"[Coder] Refactored Code:\n\n{response}"
        except:
            return "Error refactoring code"
    
    def _detect_language(self, instruction):
        """Detect programming language from instruction."""
        instruction_lower = instruction.lower()
        
        if "python" in instruction_lower: return "python"
        if "javascript" in instruction_lower or "js" in instruction_lower: return "javascript"
        if "java" in instruction_lower: return "java"
        if "c++" in instruction_lower or "cpp" in instruction_lower: return "cpp"
        if "go" in instruction_lower or "golang" in instruction_lower: return "go"
        if "rust" in instruction_lower: return "rust"
        if "bash" in instruction_lower or "shell" in instruction_lower: return "bash"
        
        return "python"  # Default
    
    def _extract_code_block(self, text):
        """Extract code from markdown code blocks."""
        match = re.search(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text
    
    def _extract_code_from_instruction(self, instruction):
        """Extract code snippet from natural language instruction."""
        # Look for code in backticks or quotes
        match = re.search(r'```.*?\n(.*?)```', instruction, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'`([^`]+)`', instruction)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_error_message(self, instruction):
        """Extract error message from instruction."""
        # Look for common error indicators
        match = re.search(r'error[:\s]+(.*?)(?:\n|$)', instruction, re.IGNORECASE)
        if match:
            return match.group(1)
        return "No error message provided"
