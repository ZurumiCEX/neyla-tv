#!/usr/bin/env python
"""Entrée standard Django : délègue aux commandes selon DJANGO_SETTINGS_MODULE."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django n'est pas installé. Active l'env virtuel ou lance via Docker."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
