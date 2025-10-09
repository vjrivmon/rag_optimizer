"""
Custom Ollama LLM Wrapper for RAGAs that ensures correct JSON formatting
"""

from typing import Any, List, Optional, Dict, Union
import json
import re
from langchain_core.language_models.llms import BaseLLM
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.outputs import LLMResult, Generation
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


class RobustOllamaWrapper(BaseLLM):
    """
    A robust wrapper for Ollama that ensures RAGAs gets properly formatted JSON responses.
    Handles common issues like:
    - JSON wrapped in markdown code blocks
    - Thinking tags in responses
    - Malformed JSON
    - Missing fields
    """

    llm: ChatOllama = Field(exclude=True)
    debug: bool = False
    model_name: str = "gemma2:27b"
    base_url: str = "https://ollama.gti-ia.upv.es:443"
    temperature: float = 0.1

    def __init__(self, model_name: str = "gemma2:27b", base_url: str = "https://ollama.gti-ia.upv.es:443",
                 temperature: float = 0.1, debug: bool = False, **kwargs):
        """Initialize the wrapper with an Ollama model"""
        llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            client_kwargs={"verify": False, "timeout": 180},
            format="json"  # Force JSON format
        )
        super().__init__(
            llm=llm,
            debug=debug,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )

    def _clean_response(self, text: str) -> str:
        """Clean and extract JSON from response"""
        if not text:
            return "{}"

        # Remove thinking tags if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # Try to find JSON object in text
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start != -1 and json_end != -1:
            text = text[json_start:json_end + 1]

        # Clean up common issues
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _fix_json_structure(self, text: str, expected_keys: Optional[List[str]] = None) -> str:
        """Try to fix common JSON structure issues"""
        try:
            # First try to parse as-is
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        # Common fixes
        # Fix single quotes
        text = text.replace("'", '"')

        # Fix trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)

        # Try to add missing quotes around keys
        text = re.sub(r'(\w+):', r'"\1":', text)

        # Fix boolean values
        text = text.replace('True', 'true').replace('False', 'false')
        text = text.replace('None', 'null')

        try:
            json.loads(text)
            return text
        except:
            # If still fails, create a minimal valid JSON
            if expected_keys:
                default = {}
                for key in expected_keys:
                    if key == "statements":
                        default[key] = []
                    elif key == "verdict":
                        default[key] = 0
                    else:
                        default[key] = ""
                return json.dumps(default)
            return "{}"

    def invoke(self, input: Any, config: Optional[Dict] = None, **kwargs) -> str:
        """Invoke the LLM and ensure JSON response"""
        # Convert input to string if needed
        if hasattr(input, 'content'):
            input_str = input.content
        elif isinstance(input, list) and len(input) > 0:
            if hasattr(input[0], 'content'):
                input_str = input[0].content
            else:
                input_str = str(input[0])
        else:
            input_str = str(input)

        # Call the underlying LLM
        response = self.llm.invoke(input_str, config=config, **kwargs)

        # Extract and clean the response text
        if isinstance(response, AIMessage):
            text = response.content
        elif hasattr(response, 'content'):
            text = response.content
        else:
            text = str(response)

        # Clean and fix JSON
        cleaned_text = self._clean_response(text)

        # Detect expected structure from the prompt
        expected_keys = None
        if "statements" in input_str.lower():
            expected_keys = ["statements"]
        if "verdict" in input_str.lower():
            expected_keys = ["statements", "verdict"]
        if "TP" in input_str or "FP" in input_str:
            expected_keys = ["TP", "FP", "FN"]

        fixed_json = self._fix_json_structure(cleaned_text, expected_keys)

        if self.debug:
            print(f"🔧 Original: {text[:200]}")
            print(f"🔧 Cleaned: {cleaned_text[:200]}")
            print(f"🔧 Fixed: {fixed_json[:200]}")

        # Validate it's proper JSON
        try:
            json.loads(fixed_json)
        except json.JSONDecodeError:
            # Last resort: return a valid but empty structure
            if expected_keys and "statements" in expected_keys:
                fixed_json = '{"statements": []}'
            else:
                fixed_json = '{}'

        return fixed_json

    async def ainvoke(self, input: Any, config: Optional[Dict] = None, **kwargs) -> str:
        """Async version of invoke"""
        return self.invoke(input, config=config, **kwargs)

    def generate(self, messages: List[List[BaseMessage]], **kwargs) -> Any:
        """Generate method for compatibility"""
        results = []
        for message_list in messages:
            response = self.invoke(message_list[-1].content if message_list else "")
            results.append([response])
        return type('obj', (object,), {'generations': results})()

    async def agenerate(self, messages: List[List[BaseMessage]], **kwargs) -> Any:
        """Async generate for compatibility"""
        return self.generate(messages, **kwargs)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Run the LLM on the given prompt and input."""
        response = self.invoke(prompt, **kwargs)
        # invoke already returns a string
        return response

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Async version of _call."""
        return self._call(prompt, stop=stop, **kwargs)

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate method required by BaseLLM."""
        generations = []
        for prompt in prompts:
            response_text = self._call(prompt, stop=stop, **kwargs)
            generations.append([Generation(text=response_text)])
        return LLMResult(generations=generations)

    async def _agenerate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Async version of generate."""
        return self._generate(prompts, stop=stop, **kwargs)

    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "robust_ollama"


def create_robust_ollama_for_ragas(
    model_name: str = "gemma2:27b",
    base_url: str = "https://ollama.gti-ia.upv.es:443",
    temperature: float = 0.1,
    debug: bool = False
) -> RobustOllamaWrapper:
    """
    Create a robust Ollama wrapper for use with RAGAs.

    Args:
        model_name: Name of the Ollama model
        base_url: URL of the Ollama server
        temperature: Temperature for generation (lower = more consistent)
        debug: Whether to print debug information

    Returns:
        A wrapped LLM suitable for RAGAs evaluation
    """
    return RobustOllamaWrapper(
        model_name=model_name,
        base_url=base_url,
        temperature=temperature,
        debug=debug
    )