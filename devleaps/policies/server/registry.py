import logging
from typing import Callable, Dict, Generator, List, Type, TypeVar, Union

from .common.models import PolicyDecision, PolicyGuidance

logger = logging.getLogger(__name__)

InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType', PolicyDecision, PolicyGuidance)

MiddlewareFunction = Callable[[InputType], Generator[InputType, None, None]]
HandlerFunction = Callable[[InputType], Generator[Union[PolicyDecision, PolicyGuidance], None, None]]


class HookRegistry:
    """Generic registry for hook handlers and middleware using class types as keys."""

    def __init__(self):
        self.handlers: Dict[Type[InputType], List[HandlerFunction]] = {}
        self.middleware: Dict[Type[InputType], List[MiddlewareFunction]] = {}

    def register_handler(self, input_class: Type[InputType], handler: HandlerFunction):
        """Register a handler for a specific input class type."""
        if input_class not in self.handlers:
            self.handlers[input_class] = []

        self.handlers[input_class].append(handler)
        logger.debug(
            f"Registered handler: {handler.__name__}",
            extra={
                "input_class": input_class.__name__,
                "handler": handler.__name__,
            }
        )

    def register_middleware(self, input_class: Type[InputType], middleware: MiddlewareFunction):
        """Register middleware for a specific input class type."""
        if input_class not in self.middleware:
            self.middleware[input_class] = []

        self.middleware[input_class].append(middleware)
        logger.debug(
            f"Registered middleware: {middleware.__name__}",
            extra={
                "input_class": input_class.__name__,
                "middleware": middleware.__name__,
            }
        )

    def get_handlers(self, input_class: Type[InputType]) -> List[HandlerFunction]:
        """Get all handlers for a specific input class type."""
        return self.handlers.get(input_class, [])

    def get_middleware(self, input_class: Type[InputType]) -> List[MiddlewareFunction]:
        """Get all middleware for a specific input class type."""
        return self.middleware.get(input_class, [])

    def register_all_middleware(self, input_class: Type[InputType], middleware_list: List[MiddlewareFunction]):
        """Register multiple middleware functions at once."""
        for middleware in middleware_list:
            self.register_middleware(input_class, middleware)

    def register_all_handlers(self, input_class: Type[InputType], handler_list: List[HandlerFunction]):
        """Register multiple handlers at once."""
        for handler in handler_list:
            self.register_handler(input_class, handler)


registry: HookRegistry = HookRegistry()