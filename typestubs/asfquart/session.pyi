"""
This type stub file was generated by pyright.
"""

import typing

"""ASFQuart - User session methods and decorators"""

class ClientSession(dict):
    uid: str | None
    dn: str | None
    fullname: str | None
    email: str
    isMember: bool
    isChair: bool
    isRoot: bool
    committees: list[str]
    projects: list[str]
    mfa: bool
    isRole: bool
    metadata: dict

    def __init__(self, raw_data: dict) -> None:
        """Initializes a client session from a raw dict. ClientSession is a subclassed dict, so that
        we can send it to quart in a format it can render."""
        ...

async def read(expiry_time=..., app=...) -> typing.Optional[ClientSession]:
    """Fetches a cookie-based session if found (and valid), and updates the last access timestamp
    for the session."""
    ...

def write(session_data: dict, app=...):  # -> None:
    """Sets a cookie-based user session for this app"""
    ...

def clear(app=...):  # -> None:
    """Clears a session"""
    ...
