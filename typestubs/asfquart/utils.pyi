"""
This type stub file was generated by pyright.
"""

import werkzeug.routing

"""Miscellaneous helpers for ASFQuart"""
LOGGER = ...
DEFAULT_MAX_CONTENT_LENGTH = ...

async def formdata():  # -> Response | dict[Any, Any]:
    """Catch-all form data converter. Converts form data of any form (json, urlencoded, mime, etc) to a dict"""
    ...

class FilenameConverter(werkzeug.routing.BaseConverter):
    """Simple converter that splits a filename into a basename and an extension. Only deals with filenames, not
    full paths. Thus, <filename> will match foo.txt, but not /foo/bar.baz"""

    regex: str = ...
    part_isolating: bool = ...
    def to_python(self, filename):  # -> tuple[Any, Any]:
        ...

def use_template(
    template,
):  # -> Callable[..., _Wrapped[Callable[..., Any], Any, Callable[..., Any], Coroutine[Any, Any, str]]]:
    ...

def render(t, data):  # -> str:
    "Simple function to render a template into a string."
    ...

class CancellableTask:
    "Wrapper for a task that does not propagate its cancellation."
    def __init__(self, coro, *, loop=..., name=...) -> None:
        "Create a task for CORO in LOOP, named NAME."
        ...
    def cancel(self):  # -> None:
        "Cancel the task, and clean up its CancelledError exception."
        ...
