"""
This type stub file was generated by pyright.
"""

import typing
from typing import Any, Callable, Coroutine, Iterable, Optional, TypeVar, Union, overload
from . import base, session

"""ASFQuart - Authentication methods and decorators"""

T = TypeVar('T')
P = TypeVar('P', bound=Callable[..., Coroutine[Any, Any, Any]])
ReqFunc = Callable[[session.ClientSession], tuple[bool, str]]

class Requirements:
    """Various pre-defined access requirements"""

    E_NOT_LOGGED_IN: str
    E_NOT_MEMBER: str
    E_NOT_CHAIR: str
    E_NO_MFA: str
    E_NOT_ROOT: str
    E_NOT_PMC: str
    E_NOT_ROLEACCOUNT: str

    @classmethod
    def mfa_enabled(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """Tests for MFA enabled in the client session"""
        ...

    @classmethod
    def committer(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """Tests for whether the user is a committer on any project"""
        ...

    @classmethod
    def member(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """Tests for whether the user is a foundation member"""
        ...

    @classmethod
    def chair(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """tests for whether the user is a chair of any top-level project"""
        ...

    @classmethod
    def root(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """tests for whether the user is a member of infra-root"""
        ...

    @classmethod
    def pmc_member(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """tests for whether the user is a PMC member of any top-level project"""
        ...

    @classmethod
    def roleacct(cls, client_session: session.ClientSession) -> tuple[bool, str]:
        """tests for whether the user is a service account"""
        ...

class AuthenticationFailed(base.ASFQuartException):
    def __init__(self, message: str = ..., errorcode: int = ...) -> None: ...

def requirements_to_iter(args: Any) -> Iterable[Any]:
    """Converts any auth req args (single arg, list, tuple) to an iterable if not already one"""
    ...

@overload
def require(func: P) -> P: ...

@overload
def require(
    func: Optional[ReqFunc] = None,
    all_of: Optional[Union[ReqFunc, Iterable[ReqFunc]]] = None,
    any_of: Optional[Union[ReqFunc, Iterable[ReqFunc]]] = None,
) -> Callable[[P], P]: ...

@overload
def require(
    func: Union[Callable[..., tuple[bool, str]], Iterable[Callable[..., tuple[bool, str]]]] = None,
    *,
    all_of: Optional[Union[Callable[..., tuple[bool, str]], Iterable[Callable[..., tuple[bool, str]]]]] = None,
    any_of: Optional[Union[Callable[..., tuple[bool, str]], Iterable[Callable[..., tuple[bool, str]]]]] = None,
) -> Callable[[P], P]: ...
