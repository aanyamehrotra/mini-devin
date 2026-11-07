"""Deliberately small requirements format for generated projects."""

import re

_NAME = r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?'
_VERSION = r'(?:===|==|!=|~=|<=|>=|<|>)\s*[A-Za-z0-9][A-Za-z0-9.*+!_-]*'
_REQUIREMENT = re.compile(
    rf'{_NAME}(?:\[{_NAME}(?:\s*,\s*{_NAME})*\])?'
    rf'(?:\s*{_VERSION}(?:\s*,\s*{_VERSION})*)?'
)


class InvalidRequirementsError(ValueError):
    pass


def validate_requirements(content: str) -> bool:
    """Accept names/extras/version constraints; reject pip directives and sources.

    Returns whether any packages were present. Does not establish package trust,
    existence, or compatibility; the wheel-only installer checks resolution.
    """
    has_packages = False
    for number, raw in enumerate(content.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if _REQUIREMENT.fullmatch(line) is None:
            raise InvalidRequirementsError(
                f'Unsupported requirement on line {number}; use a package name, '
                'optional extras and version constraints only.'
            )
        has_packages = True
    return has_packages
