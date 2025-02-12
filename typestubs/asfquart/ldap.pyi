"""
This type stub file was generated by pyright.
"""

"""ASFQuart - LDAP Authentication methods and decorators"""
DEFAULT_LDAP_URI = ...
DEFAULT_LDAP_BASE = ...
DEFAULT_LDAP_GROUP_BASE = ...
UID_RE = ...
GROUP_RE = ...
DEFAULT_MEMBER_ATTR = ...
DEFAULT_OWNER_ATTR = ...
DEFAULT_LDAP_CACHE_TTL = ...
LDAP_SUPPORTED = ...
LDAP_CACHE: dict[str, list] = ...

class LDAPClient:
    def __init__(self, username: str, password: str) -> None: ...
    async def get_affiliations(self):
        """Scans for which projects this user is a part of. Returns a dict with memberships of each
        pmc/committer role (member/owner in LDAP)"""
        ...
