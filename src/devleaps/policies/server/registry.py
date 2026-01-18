import logging
from typing import Callable, Dict, Generator, List, Optional, Set, Tuple, Type, TypeVar, Union

from .common.models import PolicyDecision, PolicyGuidance

logger = logging.getLogger(__name__)

InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType', PolicyDecision, PolicyGuidance)

HandlerFunction = Callable[[InputType], Generator[Union[PolicyDecision, PolicyGuidance], None, None]]


class HookRegistry:
    """Generic registry for hook handlers using class types as keys."""

    def __init__(self):
        # Store handlers with their bundle association: {input_class: [(handler, bundle_name_or_none), ...]}
        self.handlers: Dict[Type[InputType], List[Tuple[HandlerFunction, Optional[str]]]] = {}

    def register_handler(self, input_class: Type[InputType], handler: HandlerFunction, bundle: Optional[str] = None):
        """Register a handler for a specific input class type with optional bundle association."""
        if input_class not in self.handlers:
            self.handlers[input_class] = []

        self.handlers[input_class].append((handler, bundle))
        logger.debug(
            f"Registered handler: {handler.__name__}" + (f" (bundle: {bundle})" if bundle else ""),
            extra={
                "input_class": input_class.__name__,
                "handler": handler.__name__,
                "bundle": bundle,
            }
        )

    def get_handlers(self, input_class: Type[InputType], enabled_bundles: List[str] = []) -> List[HandlerFunction]:
        """Get handlers for input class, filtered by enabled bundles. Universal policies always included."""
        all_handlers = self.handlers.get(input_class, [])
        enabled_set = set(enabled_bundles)

        return [
            handler for handler, bundle in all_handlers
            if bundle is None or bundle in enabled_set
        ]

    def register_all_handlers(self, input_class: Type[InputType], handler_list: List[HandlerFunction], bundle: Optional[str] = None):
        """Register multiple handlers at once with optional bundle association."""
        for handler in handler_list:
            self.register_handler(input_class, handler, bundle)


registry: HookRegistry = HookRegistry()