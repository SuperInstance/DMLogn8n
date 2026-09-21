"""
GLM-4.6 Coder Bot - AI-Powered Code Generation
Automates game modifications based on player and agent requests
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class CodeRequest:
    """Request for code generation"""

    def __init__(self, requester_id: str, request_type: str,
                 parameters: Dict, context: Dict, priority: str = "normal"):
        self.id = str(uuid.uuid4())
        self.requester_id = requester_id
        self.request_type = request_type
        self.parameters = parameters
        self.context = context
        self.priority = priority
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.code = None
        self.review_status = None

class CoderBot:
    """AI-powered coder using GLM-4.6 for automation"""

    def __init__(self, model_endpoint: str, api_key: str):
        self.model_endpoint = model_endpoint
        self.api_key = api_key
        self.active_requests: Dict[str, CodeRequest] = {}
        self.completed_requests: List[Dict] = []
        self.code_templates = self.load_code_templates()
        self.safety_validator = CodeSafetyValidator()
        self.deployment_queue = List[Dict] = []

    async def process_request(self, request: CodeRequest) -> Dict:
        """Process a code generation request"""
        self.active_requests[request.id] = request

        try:
            # Generate code using GLM-4.6
            prompt = self.build_coding_prompt(request)
            raw_code = await self.call_llm(prompt)

            # Validate and sanitize code
            validated_code = await self.safety_validator.validate(raw_code)
            request.code = validated_code
            request.status = "generated"

            # Review for deployment approval
            review_result = await self.review_for_deployment(request)
            request.review_status = review_result["approved"]
            request.status = "completed" if review_result["approved"] else "requires_approval"

            # Store completed request
            if request.status == "completed":
                self.completed_requests.append({
                    "request_id": request.id,
                    "completed_at": datetime.utcnow(),
                    "code": request.code
                })
                del self.active_requests[request.id]

            return {
                "request_id": request.id,
                "status": request.status,
                "code": request.code if request.status == "completed" else None,
                "review": review_result
            }

        except Exception as e:
            logger.error(f"Error processing request {request.id}: {e}")
            request.status = "error"
            return {
                "request_id": request.id,
                "status": "error",
                "error": str(e)
            }

    def build_coding_prompt(self, request: CodeRequest) -> str:
        """Build comprehensive prompt for GLM-4.6"""
        context = self.build_context_string(request.context)
        params = self.format_parameters(request.parameters)

        prompt = f"""
As a D&D 5e expert and Python developer, you are GLM-4.6 Coder Bot.

TASK: Generate {request.request_type} code for D&D game automation

CONTEXT:
{context}

PARAMETERS:
{params}

REQUIREMENTS:
1. Code must be safe and secure (no system calls, no file access outside game directory)
2. Must follow D&D 5e rules and balance
3. Include error handling and logging
4. Add comments explaining logic
5. Use existing game APIs where available

REQUEST TYPE: {request.request_type}
PRIORITY: {request.priority}

Please generate production-ready Python code that implements this automation safely.
        """
        return prompt

    def build_context_string(self, context: Dict) -> str:
        """Build formatted context string"""
        if not context:
            return "No additional context"

        context_parts = []
        if "character_id" in context:
            context_parts.append(f"Character ID: {context['character_id']}")
        if "location" in context:
            context_parts.append(f"Location: {context['location']}")
        if "current_quest" in context:
            context_parts.append(f"Active Quest: {context['current_quest']}")
        if "party_composition" in context:
            context_parts.append(f"Party: {context['party_composition']}")

        return "\n".join(context_parts)

    def format_parameters(self, parameters: Dict) -> str:
        """Format parameters for prompt"""
        if not parameters:
            return "No specific parameters"

        parts = []
        for key, value in parameters.items():
            if isinstance(value, str):
                parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                parts.append(f"{key}: {json.dumps(value)}")
            else:
                parts.append(f"{key}: {str(value)}")

        return "\n".join(parts)

    async def call_llm(self, prompt: str) -> str:
        """Call GLM-4.6 model for code generation"""
        # This would integrate with your actual GLM-4.6 service
        # For now, return mock response
        return f"""
# Generated Python code for {prompt.split('REQUEST TYPE:')[1] if 'REQUEST TYPE:' in prompt else 'automation'}

```python
# Example automation code would be generated here
def create_automation_script(request_data):
    \"\"\"Create automation script based on request\"\"\"
    # Implementation depends on request_type
    if request_data['request_type'] == 'combat_macro':
        return generate_combat_macro(request_data)
    elif request_data['request_type'] == 'quest_helper':
        return generate_quest_helper(request_data)
    # ... more templates
```

    async def review_for_deployment(self, request: CodeRequest) -> Dict:
        """Review generated code for deployment safety"""
        # Check for dangerous patterns
        dangerous_patterns = [
            "subprocess", "os.system", "eval(", "exec(",
            "__import__", "open(", "file.write",
            "requests.get(", "urllib.request"
        ]

        code = request.code or ""
        issues_found = []

        for pattern in dangerous_patterns:
            if pattern in code.lower():
                issues_found.append(f"Potentially dangerous code: {pattern}")

        # Check D&D rules compliance
        dnd_issues = await self.check_dnd_compliance(code)

        issues_found.extend(dnd_issues)

        if issues_found or request.priority == "high":
            return {
                "approved": False,
                "issues": issues_found + dnd_issues,
                "reason": "Code requires review before deployment"
            }
        else:
            return {
                "approved": True,
                "issues": issues_found + dnd_issues,
                "reason": "Code approved for deployment"
            }

    async def check_dnd_compliance(self, code: str) -> List[str]:
        """Check if code complies with D&D 5e rules"""
        issues = []

        # Check for rule violations
        if "proficiency_bonus = 10" in code:  # Can't hardcode max bonus
            issues_found.append("Hardcoded proficiency bonus")

        # Check for overpowered items
        if "+10 longsword" in code:
            issues_found.append("Overpowered starting equipment")

        # Check for skill abuse
        if "skill_check += 20" in code:
            issues_found.append("Skill check bonus too high")

        return issues

    def load_code_templates(self) -> Dict[str, str]:
        """Load templates for common automation requests"""
        return {
            "character_macro": "def macro_template():\n    # Macro template\n    pass",
            "combat_automation": "def combat_ai():\n    # Combat AI logic\n    pass",
            "quest_generator": "def quest_template():\n    # Quest template\n    pass",
            "item_enchantment": "def enchant_item():\n    # Enchantment logic\n    pass"
        }

class CodeSafetyValidator:
    """Validates generated code for safety and security"""

    def __init__(self):
        self.restricted_modules = [
            "os", "sys", "subprocess", "socket",
            "urllib", "requests", "http.client",
            "pickle", "marshal", "shutil"
        ]
        self.restricted_functions = [
            "exec", "eval", "compile", "__import__",
            "open", "file", "input", "raw_input"
        ]

    async def validate(self, code: str) -> str:
        """Validate and sanitize code"""
        lines = code.split('\n')
        safe_lines = []

        for line in lines:
            # Check for restricted imports
            if any(module in line for module in self.restricted_modules):
                safe_lines.append(f"# RESTRICTED: {line}")
                continue

            # Check for restricted functions
            if any(func in line for func in self.restricted_functions):
                safe_lines.append(f"# RESTRICTED: {line}")
                continue

            # Additional safety checks
            if "password" in line.lower() and "=" in line:
                safe_lines.append(f"# SECURITY: Password in code")
                continue

            safe_lines.append(line)

        return '\n'.join(safe_lines)