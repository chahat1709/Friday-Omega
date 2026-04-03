"""Knowledge cache and observability collectors."""

import time
import uuid
from collections import OrderedDict, defaultdict
from typing import Any, Dict, Optional

from .config import CACHE_CAPACITY, CACHE_TTL_SECONDS


class KnowledgeCache:
    """Tiny LRU cache to short circuit repeated requests."""

    def __init__(self, capacity: int = CACHE_CAPACITY, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.store: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def _prune(self) -> None:
        now = time.time()
        expired = [key for key, entry in self.store.items() if now - entry["ts"] > self.ttl]
        for key in expired:
            self.store.pop(key, None)
        while len(self.store) > self.capacity:
            self.store.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        self._prune()
        entry = self.store.get(key)
        if not entry:
            return None
        self.store.move_to_end(key)
        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        self.store[key] = {"value": value, "ts": time.time()}
        self.store.move_to_end(key)
        self._prune()


class ObservabilityHub:
    """Collects lightweight traces and aggregates intent usage."""

    def __init__(self) -> None:
        self.traces: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.intent_heatmap = defaultdict(int)
        self.max_traces = 32

    @staticmethod
    def new_trace_id() -> str:
        return uuid.uuid4().hex[:8]

    def record_trace(self, trace_id: str, payload: Dict[str, Any]) -> None:
        self.traces[trace_id] = payload
        self.traces.move_to_end(trace_id)
        while len(self.traces) > self.max_traces:
            self.traces.popitem(last=False)

    def add_intent(self, intent: str) -> None:
        self.intent_heatmap[intent] += 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            "heatmap": dict(sorted(self.intent_heatmap.items(), key=lambda item: item[1], reverse=True)),
            "recent_traces": list(self.traces.values())[-10:],
        }


knowledge_cache = KnowledgeCache()
observability = ObservabilityHub()
