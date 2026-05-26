#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


BASHRC_PATH = os.path.expanduser("~/.bashrc")
BACKUP_DIR = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "io.github.aayamrajshakya.aliasmanager")
MARKER = "# [alias-manager]"


@dataclass
class Alias:
    name: str
    command: str
    comment: str = ""

    def to_bashrc_line(self) -> str:
        if self.comment:
            return f"alias {self.name}='{self.command}'  # {self.comment} {MARKER}"
        return f"alias {self.name}='{self.command}'  {MARKER}"

    @staticmethod
    def from_line(line: str) -> Optional["Alias"]:
        """Parse a bashrc alias line into an Alias object."""
        # Strip marker
        clean = line.replace(MARKER, "").strip()
        m = (
            re.match(r"^alias\s+(\w+)='([^']*)'(?:\s*#\s*(.*))?$", clean) or
            re.match(r'^alias\s+(\w+)="([^"]*)"(?:\s*#\s*(.*))?$', clean)
        )
        if m:
            return Alias(name=m.group(1), command=m.group(2), comment=(m.group(3) or "").strip())
        return None


def backup_bashrc():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_DIR, f".bashrc.{ts}.bak")
    if os.path.exists(BASHRC_PATH):
        shutil.copy2(BASHRC_PATH, backup)
    return backup


def load_aliases() -> list[Alias]:
    """Load all aliases from ~/.bashrc — both managed and unmanaged."""
    aliases = []
    if not os.path.exists(BASHRC_PATH):
        return aliases

    with open(BASHRC_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("alias "):
                alias = Alias.from_line(line)
                if alias:
                    aliases.append(alias)
    return aliases


def save_alias(alias: Alias):
    """Append a new managed alias to ~/.bashrc."""
    backup_bashrc()
    with open(BASHRC_PATH, "a") as f:
        f.write(f"\n{alias.to_bashrc_line()}\n")


def delete_alias(alias: Alias):
    """Remove an alias line from ~/.bashrc."""
    backup_bashrc()
    if not os.path.exists(BASHRC_PATH):
        return

    with open(BASHRC_PATH, "r") as f:
        lines = f.readlines()

    # Match lines that define this alias (managed or plain)
    pattern = re.compile(rf"^alias\s+{re.escape(alias.name)}=")
    new_lines = [l for l in lines if not pattern.match(l.strip())]

    with open(BASHRC_PATH, "w") as f:
        f.writelines(new_lines)


def update_alias(old: Alias, new: Alias):
    """Replace an existing alias line in ~/.bashrc."""
    backup_bashrc()
    if not os.path.exists(BASHRC_PATH):
        return

    with open(BASHRC_PATH, "r") as f:
        lines = f.readlines()

    pattern = re.compile(rf"^alias\s+{re.escape(old.name)}=")
    new_lines = []
    replaced = False
    for line in lines:
        if pattern.match(line.strip()) and not replaced:
            new_lines.append(new.to_bashrc_line() + "\n")
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        new_lines.append(new.to_bashrc_line() + "\n")

    with open(BASHRC_PATH, "w") as f:
        f.writelines(new_lines)


def alias_name_exists(name: str, exclude: str = "") -> bool:
    for a in load_aliases():
        if a.name == name and a.name != exclude:
            return True
    return False
