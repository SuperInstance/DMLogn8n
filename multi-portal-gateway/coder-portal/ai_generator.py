"""
AI Generator - Integrates with AI services for code generation and improvement.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import uuid

from ..gateway.config import settings

logger = logging.getLogger(__name__)

class AIGenerator:
    """Handles AI-powered code generation and improvement."""

    def __init__(self):
        self.ai_service_url = settings.AI_SERVICE_URL
        self.ai_model = settings.AI_MODEL
        self.generation_history: List[Dict[str, Any]] = []
        self.active_generations: Dict[str, asyncio.Task] = {}
        self.supported_languages = ["python", "javascript", "typescript", "java", "cpp", "go", "rust"]
        self.is_initialized = False

    async def initialize(self):
        """Initialize the AI generator."""
        logger.info("Initializing AI Generator...")

        # Test AI service connection
        try:
            await self._test_ai_connection()
            logger.info("AI service connection established")
        except Exception as e:
            logger.warning(f"Could not connect to AI service: {str(e)}")
            logger.info("AI Generator will work in mock mode")

        self.is_initialized = True
        logger.info("AI Generator initialized")

    async def _test_ai_connection(self):
        """Test connection to AI service."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ai_service_url}/api/tags", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Connected to AI service. Available models: {list(data.get('models', {}).keys())}")
                else:
                    raise Exception(f"AI service returned status {response.status}")

    async def generate_code(self, prompt: str, language: str = "python", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate code using AI."""
        try:
            generation_id = str(uuid.uuid4())
            start_time = datetime.now()

            logger.info(f"Generating code for prompt: {prompt[:100]}...")

            # Build the generation request
            full_prompt = self._build_generation_prompt(prompt, language, context or {})

            # Call AI service
            generated_code = await self._call_ai_service(full_prompt)

            # Process the result
            result = {
                "generation_id": generation_id,
                "prompt": prompt,
                "language": language,
                "code": generated_code,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "generation_time": (datetime.now() - start_time).total_seconds()
            }

            # Add to history
            self.generation_history.append(result)

            # Keep history limited
            if len(self.generation_history) > 100:
                self.generation_history = self.generation_history[-50:]

            logger.info(f"Code generated successfully in {result['generation_time']:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Failed to generate code: {str(e)}")
            # Return mock response for testing
            return await self._generate_mock_code(prompt, language, context)

    def _build_generation_prompt(self, prompt: str, language: str, context: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for AI generation."""
        language_instructions = {
            "python": "Generate Python code. Use proper PEP 8 formatting. Include type hints where appropriate.",
            "javascript": "Generate modern JavaScript code (ES6+). Use proper syntax and best practices.",
            "typescript": "Generate TypeScript code. Include proper type definitions and interfaces.",
            "java": "Generate Java code. Follow Java conventions and include proper package declarations.",
            "cpp": "Generate C++ code. Use modern C++ standards and include necessary headers.",
            "go": "Generate Go code. Follow Go conventions and include proper error handling.",
            "rust": "Generate Rust code. Follow Rust conventions and include proper error handling."
        }

        base_prompt = f"""
You are an expert programmer helping to generate code. Please write clean, well-commented code.

Language: {language.upper()}
Instructions: {language_instructions.get(language, "Generate clean, well-commented code.")}

User Request: {prompt}

"""
        if context:
            base_prompt += f"\nAdditional Context:\n{json.dumps(context, indent=2)}\n"

        base_prompt += f"""
Please provide:
1. The complete code solution
2. Brief explanation of the approach
3. Any important notes or considerations

Format your response as JSON:
{{
    "code": "the generated code here",
    "explanation": "brief explanation of the code",
    "notes": "any important notes"
}}
"""

        return base_prompt

    async def _call_ai_service(self, prompt: str) -> str:
        """Call the AI service for code generation."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.ai_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 2048
                    }
                }

                async with session.post(
                    f"{self.ai_service_url}/api/generate",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_ai_response(data.get("response", ""))
                    else:
                        raise Exception(f"AI service returned status {response.status}")

        except Exception as e:
            logger.error(f"Failed to call AI service: {str(e)}")
            raise

    def _parse_ai_response(self, response: str) -> str:
        """Parse the AI response to extract code."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get("code", response)
            else:
                # Extract code from markdown code blocks
                import re
                code_pattern = r'```(?:\w+)?\n(.*?)\n```'
                matches = re.findall(code_pattern, response, re.DOTALL)
                if matches:
                    return matches[0].strip()
                else:
                    return response.strip()
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return response.strip()

    async def _generate_mock_code(self, prompt: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock code for testing when AI service is unavailable."""
        logger.info("Generating mock code (AI service unavailable)")

        mock_code = {
            "python": f"""
# Mock generated Python code for: {prompt}
def main():
    \"\"\"Generated function based on the prompt: {prompt}\"\"\"
    print("This is mock generated code")
    # TODO: Implement actual functionality
    pass

if __name__ == "__main__":
    main()
""",
            "javascript": f"""
// Mock generated JavaScript code for: {prompt}
function main() {{
    console.log("This is mock generated code");
    // TODO: Implement actual functionality
}}

main();
""",
            "typescript": f"""
// Mock generated TypeScript code for: {prompt}
interface MockResponse {{
    message: string;
}}

function main(): MockResponse {{
    console.log("This is mock generated code");
    // TODO: Implement actual functionality
    return {{ message: "Mock response" }};
}}

main();
"""
        }

        code = mock_code.get(language, f"// Mock generated {language} code for: {prompt}\n// TODO: Implement actual functionality")

        return {
            "generation_id": str(uuid.uuid4()),
            "prompt": prompt,
            "language": language,
            "code": code,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "generation_time": 0.1,
            "mock": True
        }

    async def improve_code(self, code: str, improvements: List[str]) -> Dict[str, Any]:
        """Improve existing code using AI."""
        try:
            improvement_id = str(uuid.uuid4())
            start_time = datetime.now()

            improvement_prompt = f"""
Please improve the following code based on these requirements:
{json.dumps(improvements, indent=2)}

Original Code:
{code}

Please provide:
1. The improved code
2. Explanation of improvements made
3. Any breaking changes

Format your response as JSON:
{{
    "improved_code": "the improved code here",
    "improvements_made": ["list of improvements"],
    "explanation": "explanation of changes",
    "breaking_changes": ["list of breaking changes if any"]
}}
"""

            # Call AI service
            result = await self._call_ai_service(improvement_prompt)

            # Parse the improvement result
            try:
                improvement_data = json.loads(result)
                improved_code = improvement_data.get("improved_code", code)
            except:
                improved_code = result

            improvement_result = {
                "improvement_id": improvement_id,
                "original_code": code,
                "improved_code": improved_code,
                "improvements_requested": improvements,
                "timestamp": datetime.now().isoformat(),
                "improvement_time": (datetime.now() - start_time).total_seconds()
            }

            logger.info(f"Code improved successfully in {improvement_result['improvement_time']:.2f}s")
            return improvement_result

        except Exception as e:
            logger.error(f"Failed to improve code: {str(e)}")
            return {
                "improvement_id": str(uuid.uuid4()),
                "original_code": code,
                "improved_code": code,
                "improvements_requested": improvements,
                "timestamp": datetime.now().isoformat(),
                "improvement_time": 0.1,
                "error": str(e)
            }

    async def explain_code(self, code: str, language: str = "python") -> str:
        """Generate explanation for code using AI."""
        try:
            explanation_prompt = f"""
Please explain the following {language} code in detail:

{code}

Please provide:
1. Overall purpose of the code
2. Step-by-step explanation of what it does
3. Key concepts or patterns used
4. Potential improvements or issues

Format your response as a clear, detailed explanation.
"""

            explanation = await self._call_ai_service(explanation_prompt)
            return explanation

        except Exception as e:
            logger.error(f"Failed to explain code: {str(e)}")
            return f"Unable to generate explanation due to error: {str(e)}"

    async def generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Generate unit tests for the given code."""
        try:
            test_id = str(uuid.uuid4())

            test_prompt = f"""
Generate comprehensive unit tests for the following {language} code:

{code}

Please provide:
1. Complete test code
2. Test cases for normal scenarios
3. Test cases for edge cases and error conditions
4. Mock objects if needed

Format your response as JSON:
{{
    "test_code": "the complete test code",
    "test_cases": ["list of test cases"],
    "setup_code": "any setup code needed",
    "explanation": "explanation of test approach"
}}
"""

            result = await self._call_ai_service(test_prompt)

            try:
                test_data = json.loads(result)
                test_code = test_data.get("test_code", result)
            except:
                test_code = result

            test_result = {
                "test_id": test_id,
                "original_code": code,
                "test_code": test_code,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Tests generated for {language} code")
            return test_result

        except Exception as e:
            logger.error(f"Failed to generate tests: {str(e)}")
            return {
                "test_id": str(uuid.uuid4()),
                "original_code": code,
                "test_code": f"# Mock test code for {language}\n# TODO: Write actual tests",
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def optimize_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Optimize code for performance."""
        try:
            optimization_id = str(uuid.uuid4())

            optimization_prompt = f"""
Optimize the following {language} code for better performance:

{code}

Please provide:
1. Optimized version of the code
2. Explanation of performance improvements
3. Before/after complexity analysis if applicable
4. Any trade-offs made

Format your response as JSON:
{{
    "optimized_code": "the optimized code",
    "improvements": ["list of performance improvements"],
    "complexity_analysis": "time and space complexity analysis",
    "trade_offs": ["list of any trade-offs made"]
}}
"""

            result = await self._call_ai_service(optimization_prompt)

            try:
                optimization_data = json.loads(result)
                optimized_code = optimization_data.get("optimized_code", code)
            except:
                optimized_code = result

            optimization_result = {
                "optimization_id": optimization_id,
                "original_code": code,
                "optimized_code": optimized_code,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Code optimization completed for {language}")
            return optimization_result

        except Exception as e:
            logger.error(f"Failed to optimize code: {str(e)}")
            return {
                "optimization_id": str(uuid.uuid4()),
                "original_code": code,
                "optimized_code": code,
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def get_generation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get AI generation history."""
        return self.generation_history[-limit:]

    async def clear_history(self):
        """Clear generation history."""
        self.generation_history.clear()

    async def get_status(self) -> Dict[str, Any]:
        """Get AI generator status."""
        return {
            "initialized": self.is_initialized,
            "ai_service_url": self.ai_service_url,
            "ai_model": self.ai_model,
            "supported_languages": self.supported_languages,
            "total_generations": len(self.generation_history),
            "active_generations": len(self.active_generations),
            "service_available": await self._check_service_availability()
        }

    async def _check_service_availability(self) -> bool:
        """Check if AI service is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ai_service_url}/api/tags", timeout=3) as response:
                    return response.status == 200
        except:
            return False