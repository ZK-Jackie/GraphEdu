"""CLI Utils Models"""

from typing import TypedDict


class TyperContext(TypedDict, total=False):
    """CLI Utils Context"""

    config: str
    verbose: bool
