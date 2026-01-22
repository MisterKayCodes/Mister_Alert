import asyncio
from collections import defaultdict
from typing import Callable, Type, Dict, List, Any


class EventBus:
    def __init__(self):
        # event_type -> list of handlers
        self._subscribers: Dict[Type, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable):
        """Register a handler for an event type."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    async def publish(self, event: Any):
        """Publish an event to all subscribers."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)


# Global event bus instance
event_bus = EventBus()
