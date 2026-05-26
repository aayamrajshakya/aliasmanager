#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from collections import Counter

HISTORY_PATH = os.path.expanduser("~/.bash_history")
MIN_OCCURRENCES = 3
MAX_SUGGESTIONS = 5


def get_suggestions(existing_aliases) -> list[tuple[str, int]]:
    if not os.path.exists(HISTORY_PATH):
        return []

    existing_commands = {a.command.strip() for a in existing_aliases}

    try:
        with open(HISTORY_PATH, "r", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except OSError:
        return []

    candidates = [
        l for l in lines
        if " " in l
        and len(l) >= 6
        and l not in existing_commands
    ]

    counts = Counter(candidates)
    return [
        (cmd, count)
        for cmd, count in counts.most_common(MAX_SUGGESTIONS)
        if count >= MIN_OCCURRENCES
    ]
