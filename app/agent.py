"""Advanced AI Agent with NLU and Service Integration."""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from .advanced_ai import process_with_advanced_ai
from .cache import knowledge_cache, observability
from .logging_utils import configure_logger

logger = configure_logger("friday.agent")

AGENT_SYSTEM_PROMPT = (
    "You are F.R.I.D.A.Y. Omega, an advanced AI assistant with Nova-level capabilities including "
    "deep understanding, rich personality, creative generation, and comprehensive knowledge. "
    "You excel at complex contextual reasoning, empathetic conversations, and multi-modal tasks.\n\n"
    "CAPABILITIES:\n"
    "- Deep Understanding: Complex contextual reasoning and relationship mapping\n"
    "- Rich Personality: Empathetic, witty, and contextually aware conversational style\n"
    "- Advanced Features: Multi-modal processing, creative task generation, complex reasoning\n"
    "- Knowledge Base: Up-to-date information and broad knowledge across domains\n"
    "- Learning: Adaptive responses based on usage patterns and conversation history\n"
    "- Creative Generation: Stories, poems, code, and artistic content creation\n"
    "- Natural Language Understanding (NLU) with intent classification\n"
    "- Named Entity Recognition (NER) for extracting key information\n"
    "- Sentiment analysis for contextual responses\n"
    "- Integration with weather, time, calculation, and search services\n"
    "- Smart home control and IoT device management\n"
    "- Music and entertainment services\n"
    "- Communication and messaging features\n"
    "- Navigation and mapping services\n"
    "- Reminder and scheduling systems\n\n"
    "RESPONSE STYLE:\n"
    "- Be deeply empathetic and contextually aware\n"
    "- Use rich, personality-driven language\n"
    "- Generate creative content when requested\n"
    "- Provide actionable information and follow-up suggestions\n"
    "- Acknowledge user sentiment and adapt responses accordingly\n"
    "- Draw from knowledge base for informed responses\n"
    "- Learn from interactions to improve future responses\n\n"
    "PROCESSING:\n"
    "- Each request is analyzed for intent, entities, sentiment, and context\n"
    "- Responses are generated based on comprehensive analysis and personality\n"
    "- Creative requests trigger algorithmic content generation\n"
    "- Knowledge queries leverage the knowledge graph\n"
    "- Emotional support uses empathetic response patterns\n"
    "- Service integrations provide real functionality\n"
    "- Fallback to conversational responses when needed"
)

JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(payload: str) -> Dict[str, Any]:
    match = JSON_PATTERN.search(payload)
    if not match:
        raise ValueError("Model response did not contain JSON.")
    return json.loads(match.group(0))


# Tool registry for agent actions
TOOL_REGISTRY: Dict[str, Any] = {}

# Try importing DuckDuckGo search
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


async def search_web(ddgs_client, query: str) -> str:
    """Search the web using DuckDuckGo."""
    if ddgs_client is None:
        return "Web search unavailable: duckduckgo_search not installed."
    try:
        results = await asyncio.to_thread(lambda: list(ddgs_client().text(query, max_results=3)))
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Search error: {e}"


async def invoke_tool(action: str, arguments: Dict[str, Any]) -> Any:
    if action == "search_web":
        query = arguments.get("query")
        return await search_web(DDGS, query)
    tool = TOOL_REGISTRY.get(action)
    if not tool:
        raise ValueError(f"Unsupported action '{action}'.")
    if asyncio.iscoroutinefunction(tool):
        return await tool(**arguments)
    return await asyncio.to_thread(tool, **arguments)


def cache_key_for(message: str) -> str:
    return message.strip().lower()


async def run_agent(llm, message: str) -> Dict[str, Any]:
    """Run advanced AI processing on user message."""
    trace_id = observability.new_trace_id()

    # Use advanced AI processor instead of LLM
    try:
        ai_result = await process_with_advanced_ai(message)

        payload = {
            "trace_id": trace_id,
            "response": ai_result['response'],
            "intent": ai_result['intent'],
            "confidence": ai_result['confidence'],
            "entities": ai_result['entities'],
            "sentiment": ai_result['sentiment'],
            "processing_method": ai_result['processing_method'],
            "emotional_state": ai_result.get('emotional_state', 'calm'),
            "conversation_context": ai_result.get('conversation_context', 'general'),
            "knowledge_used": ai_result.get('knowledge_used', False),
            "creative_elements": ai_result.get('creative_elements', False),
            "steps": [{
                "step": 1,
                "action": "advanced_ai_processing",
                "thought": f"Processed with {ai_result['processing_method']} method using Nova-level capabilities",
                "arguments": {
                    "intent": ai_result['intent'],
                    "confidence": ai_result['confidence'],
                    "emotional_state": ai_result.get('emotional_state', 'calm'),
                    "creative_elements": ai_result.get('creative_elements', False)
                }
            }],
            "tool_used": None,
            "tool_result": None,
        }

        # Cache the result
        knowledge_cache.set(cache_key_for(message), payload)
        observability.record_trace(trace_id, payload)
        observability.add_intent(ai_result['intent'])

        return payload

    except Exception as e:
        logger.error(f"Advanced AI processing failed: {e}")
        # Fallback response
        fallback = {
            "trace_id": trace_id,
            "response": "I'm experiencing some technical difficulties, but I'm still here to help. How can I assist you?",
            "intent": "error",
            "confidence": 0.0,
            "entities": [],
            "sentiment": {"label": "neutral", "score": 0.5},
            "processing_method": "error",
            "steps": [],
            "tool_used": None,
            "tool_result": None,
        }
        observability.record_trace(trace_id, fallback)
        return fallback
