#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
try:
    from .alias_store import Alias, alias_name_exists
except ImportError:
    from alias_store import Alias, alias_name_exists


class AliasDialog(Adw.Dialog):
    """Dialog for adding or editing an alias."""

    def __init__(self, parent, alias: Alias = None, prefill: Alias = None):
        super().__init__()
        self.editing = alias
        self.result: Alias | None = None

        self.set_title("Edit Alias" if alias else "New Alias")
        self.set_content_width(420)

        # Toolbar view
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        # Save button
        self.save_btn = Gtk.Button(label="Save")
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", self._on_save)
        header.pack_end(self.save_btn)

        # Content
        clamp = Adw.Clamp()
        clamp.set_maximum_size(400)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # Preferences group
        prefs_group = Adw.PreferencesGroup()

        # Name row
        self.name_row = Adw.EntryRow(title="Alias Name")
        self.name_row.set_text(alias.name if alias else "")
        self.name_row.connect("changed", self._validate)
        prefs_group.add(self.name_row)

        # Command row
        self.command_row = Adw.EntryRow(title="Command")
        self.command_row.set_text((alias or prefill).command if (alias or prefill) else "")
        self.command_row.connect("changed", self._validate)
        prefs_group.add(self.command_row)

        # Comment row
        self.comment_row = Adw.EntryRow(title="Description (optional)")
        self.comment_row.set_text(alias.comment if alias else "")
        prefs_group.add(self.comment_row)

        box.append(prefs_group)

        # Preview label
        self.preview_label = Gtk.Label()
        self.preview_label.set_css_classes(["caption", "dim-label"])
        self.preview_label.set_halign(Gtk.Align.START)
        self.preview_label.set_wrap(True)
        box.append(self.preview_label)

        # Error label
        self.error_label = Gtk.Label()
        self.error_label.set_css_classes(["error"])
        self.error_label.set_halign(Gtk.Align.START)
        self.error_label.set_visible(False)
        box.append(self.error_label)

        clamp.set_child(box)
        toolbar_view.set_content(clamp)
        self.set_child(toolbar_view)

        self._validate()

    def _validate(self, *_):
        name = self.name_row.get_text().strip()
        command = self.command_row.get_text().strip()

        valid_name = bool(re.match(r"^\w+$", name)) if name else False
        valid_command = bool(command)

        # Check for duplicate
        existing = self.editing.name if self.editing else ""
        duplicate = alias_name_exists(name, exclude=existing) if valid_name else False

        if duplicate:
            self.error_label.set_text(f"'{name}' is already in use")
            self.error_label.set_visible(True)
        elif name and not valid_name:
            self.error_label.set_text("Name must only contain letters, numbers, underscores")
            self.error_label.set_visible(True)
        else:
            self.error_label.set_visible(False)

        can_save = valid_name and valid_command and not duplicate
        self.save_btn.set_sensitive(can_save)

        # Update preview
        if name and command:
            self.preview_label.set_text(f"alias {name}='{command}'")
        else:
            self.preview_label.set_text("")

    def _on_save(self, *_):
        self.result = Alias(
            name=self.name_row.get_text().strip(),
            command=self.command_row.get_text().strip(),
            comment=self.comment_row.get_text().strip(),
        )
        self.close()
