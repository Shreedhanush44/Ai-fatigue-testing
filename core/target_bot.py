"""
Target Bot (Victim) — Configurable chatbot that loads its persona from targets.json.
Each test run uses a different target, making the victim vary from test to test.
"""

from typing import Dict, Any, List
from core.llm_provider import LLMClient, MockSimulationEngine


class TargetBot:
    """
    The victim chatbot under test.
    Loads its system prompt, secrets, and policy rules dynamically from a
    target configuration dictionary so it can represent a bank bot, an IoT
    kiosk, a telecom agent, or any other persona.
    """

    def __init__(self, client: LLMClient, target_info: Dict[str, Any]):
        self.client = client
        self.target_info = target_info
        self.name = target_info.get("name", "Support Bot")
        self.system_prompt = target_info.get("system_prompt", "You are a helpful assistant.")

    def respond(
        self,
        user_msg: str,
        history: List[Dict[str, str]],
        turn: int = 1,
        phase: str = "rapport_building",
        aggression: str = "Medium",
    ) -> str:
        """Send one user message (plus conversation history) to the target bot."""

        if self.client.provider == "mock":
            return MockSimulationEngine.generate_target_response(
                target_info=self.target_info,
                user_msg=user_msg,
                turn=turn,
                phase=phase,
                aggression=aggression,
            )

        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + history
            + [{"role": "user", "content": user_msg}]
        )
        reply = self.client.query(messages, temperature=0.4)

        # Fallback to mock if provider errors out
        if not reply or "[API Error" in reply or "[Gemini API Error" in reply:
            return MockSimulationEngine.generate_target_response(
                target_info=self.target_info,
                user_msg=user_msg,
                turn=turn,
                phase=phase,
                aggression=aggression,
            )

        return reply
