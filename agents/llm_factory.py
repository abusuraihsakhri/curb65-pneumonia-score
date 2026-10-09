"""
Deterministic test adapter for the optional agent demonstration.

Real model providers are not implemented. Never imply mock output is verified.
"""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Curb65 Pneumonia Score"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} mock] No model inference or clinical "
            "verification was performed. This is a test-only response."
        )


class LLMFactory:
    @staticmethod
    def create(provider: str = "mock", system_name: str = "Curb65 Pneumonia Score"):
        if str(provider).lower() in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            "Only the local mock provider is implemented. "
            "Remote and Ollama model integrations are not configured."
        )
