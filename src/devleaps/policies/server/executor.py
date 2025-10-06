import logging
from typing import List, Union

from .common.models import PolicyDecision, PolicyGuidance
from .registry import registry

logger = logging.getLogger(__name__)


def execute_handlers_generic(input_data) -> List[Union[PolicyDecision, PolicyGuidance]]:
    """
    Execute middleware and handlers with generic event input and return generic results.

    This is the core policy execution pipeline:
    1. Process input through middleware (can transform/split inputs)
    2. Execute all registered handlers
    3. Return raw policy results (decisions and guidance)

    Aggregation of results is done by the mapper layer for each editor.
    """
    processed_inputs = _process_middleware_pipeline(input_data)
    all_results = _execute_all_handlers(processed_inputs)
    return all_results


def _process_middleware_pipeline(input_data):
    """Process input through middleware pipeline."""
    current_inputs = [input_data]
    middleware_functions = registry.get_middleware(type(input_data))

    for middleware in middleware_functions:
        next_inputs = []
        for input_item in current_inputs:
            try:
                yielded_inputs = list(middleware(input_item))
                next_inputs.extend(yielded_inputs)
                logger.debug(
                    f"Middleware {middleware.__name__} yielded {len(yielded_inputs)} inputs",
                    extra={
                        "middleware": middleware.__name__,
                        "input_count": len(yielded_inputs),
                    }
                )
            except Exception as e:
                logger.error(
                    f"Error in middleware {middleware.__name__}: {e}",
                    extra={
                        "middleware": middleware.__name__,
                        "error": str(e),
                    },
                    exc_info=True
                )
                next_inputs.append(input_item)
        current_inputs = next_inputs

    return current_inputs


def _execute_all_handlers(processed_inputs):
    """Execute all handlers on processed inputs and collect results."""
    if not processed_inputs:
        return []

    handlers = registry.get_handlers(type(processed_inputs[0]))
    all_results = []

    for processed_input in processed_inputs:
        for handler in handlers:
            try:
                yielded_results = list(handler(processed_input))
                all_results.extend(yielded_results)
                logger.debug(
                    f"Handler {handler.__name__} yielded {len(yielded_results)} results",
                    extra={
                        "handler": handler.__name__,
                        "result_count": len(yielded_results),
                    }
                )
            except Exception as e:
                logger.error(
                    f"Error in handler {handler.__name__}: {e}",
                    extra={
                        "handler": handler.__name__,
                        "error": str(e),
                    },
                    exc_info=True
                )
                continue

    return all_results
