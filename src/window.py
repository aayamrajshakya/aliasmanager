#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import html
import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib, Pango
try:
    from .alias_store import (
        Alias, load_aliases, save_alias,
        delete_alias, update_alias, BASHRC_PATH
    )
    from .alias_dialog import AliasDialog
    from .history import get_suggestions
except ImportError:
    from alias_store import (
        Alias, load_aliases, save_alias,
        delete_alias, update_alias, BASHRC_PATH
    )
    from alias_dialog import AliasDialog
    from history import get_suggestions


class AliasRow(Adw.ActionRow):
    def __init__(self, alias: Alias, selection_mode: bool = False, selected: bool = False, on_selection_changed=None):
        super().__init__()
        self.alias = alias
        self._on_selection_changed = on_selection_changed
        self._build(alias, selection_mode, selected)

    def _build(self, alias: Alias, selection_mode: bool, selected: bool):
        self.set_title(alias.name)
        self.set_subtitle(html.escape(alias.command))
        self.add_css_class("alias-row")

        if selection_mode:
            check = Gtk.CheckButton()
            check.set_active(selected)
            check.set_valign(Gtk.Align.CENTER)
            check.connect("toggled", lambda c: self._on_selection_changed and self._on_selection_changed(alias.name, c.get_active()))
            self.add_prefix(check)
            self.set_activatable_widget(check)
            return

        if alias.comment:
            badge = Gtk.Label(label=alias.comment)
            badge.set_css_classes(["caption", "dim-label"])
            badge.set_ellipsize(Pango.EllipsizeMode.END)
            badge.set_max_width_chars(30)
            badge.set_valign(Gtk.Align.CENTER)
            self.add_suffix(badge)

        edit_btn = Gtk.Button()
        edit_btn.set_icon_name("document-edit-symbolic")
        edit_btn.set_tooltip_text("Edit alias")
        edit_btn.set_valign(Gtk.Align.CENTER)
        edit_btn.add_css_class("flat")
        edit_btn.connect("clicked", self._on_edit)
        self.add_suffix(edit_btn)

        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.set_tooltip_text("Delete alias")
        delete_btn.set_valign(Gtk.Align.CENTER)
        delete_btn.add_css_class("flat")
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete)
        self.add_suffix(delete_btn)

        copy_btn = Gtk.Button()
        copy_btn.set_icon_name("edit-copy-symbolic")
        copy_btn.set_tooltip_text("Copy to clipboard")
        copy_btn.set_valign(Gtk.Align.CENTER)
        copy_btn.add_css_class("flat")
        copy_btn.connect("clicked", self._on_copy)
        self.add_suffix(copy_btn)

    def _on_edit(self, *_):
        win = self.get_root()
        win.open_edit_dialog(self.alias)

    def _on_delete(self, *_):
        win = self.get_root()
        win.confirm_delete(self.alias)

    def _on_copy(self, btn):
        clip = self.get_clipboard()
        clip.set(f"alias {self.alias.name}='{self.alias.command}'")
        win = self.get_root()
        win.show_toast("Copied to clipboard")


class AliasManagerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Alias Manager")
        self.set_default_size(680, 600)

        self._all_aliases: list[Alias] = []
        self._search_query = ""
        self._reload_timeout_id = None
        self._selection_mode = False
        self._selected: set[str] = set()

        self._build_ui()
        self._load()
        self._watch_bashrc()

    def _build_ui(self):
        # Toast overlay wraps everything
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Toolbar view
        toolbar_view = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar_view)

        # Header bar
        header = Adw.HeaderBar()

        # Normal mode buttons
        self.search_btn = Gtk.ToggleButton()
        self.search_btn.set_icon_name("system-search-symbolic")
        self.search_btn.set_tooltip_text("Search aliases (Ctrl+F)")
        self.search_btn.connect("toggled", self._on_search_toggled)
        header.pack_start(self.search_btn)

        self.add_btn = Gtk.Button()
        self.add_btn.set_icon_name("list-add-symbolic")
        self.add_btn.set_tooltip_text("Add new alias (Ctrl+N)")
        self.add_btn.add_css_class("suggested-action")
        self.add_btn.connect("clicked", self._on_add_clicked)
        header.pack_end(self.add_btn)

        menu = Gio.Menu()
        menu.append("Open ~/.bashrc", "app.open-bashrc")
        menu.append("About", "app.about")
        self.menu_btn = Gtk.MenuButton()
        self.menu_btn.set_icon_name("open-menu-symbolic")
        self.menu_btn.set_menu_model(menu)
        header.pack_end(self.menu_btn)

        self.select_btn = Gtk.Button()
        self.select_btn.set_icon_name("object-select-symbolic")
        self.select_btn.set_tooltip_text("Select aliases")
        self.select_btn.connect("clicked", self._enter_selection_mode)
        header.pack_end(self.select_btn)

        # Selection mode buttons (hidden by default)
        self.cancel_select_btn = Gtk.Button(label="Cancel")
        self.cancel_select_btn.connect("clicked", self._exit_selection_mode)
        self.cancel_select_btn.set_visible(False)
        header.pack_start(self.cancel_select_btn)

        self.delete_selected_btn = Gtk.Button(label="Delete")
        self.delete_selected_btn.add_css_class("destructive-action")
        self.delete_selected_btn.set_sensitive(False)
        self.delete_selected_btn.set_visible(False)
        self.delete_selected_btn.connect("clicked", self._on_delete_selected)
        header.pack_end(self.delete_selected_btn)

        toolbar_view.add_top_bar(header)

        # Window actions for keyboard shortcuts
        new_action = Gio.SimpleAction.new("new-alias", None)
        new_action.connect("activate", self._on_add_clicked)
        self.add_action(new_action)

        toggle_search_action = Gio.SimpleAction.new("toggle-search", None)
        toggle_search_action.connect("activate", lambda *_: self.search_btn.set_active(not self.search_btn.get_active()))
        self.add_action(toggle_search_action)

        # Search bar
        self.search_bar = Gtk.SearchBar()
        self.search_bar.set_key_capture_widget(self)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_bar.set_child(self.search_entry)
        self.search_bar.connect_entry(self.search_entry)
        toolbar_view.add_top_bar(self.search_bar)

        # Main scrolled content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.clamp = Adw.Clamp()
        self.clamp.set_maximum_size(680)
        self.clamp.set_margin_top(12)
        self.clamp.set_margin_bottom(24)
        self.clamp.set_margin_start(12)
        self.clamp.set_margin_end(12)

        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.clamp.set_child(self.outer_box)
        scroll.set_child(self.clamp)
        toolbar_view.set_content(scroll)

        # Status page (shown when empty)
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("utilities-terminal-symbolic")
        self.status_page.set_title("No Aliases Yet")
        self.status_page.set_description(f"Add your first alias to get started.\nThey'll be saved to {BASHRC_PATH}")
        add_first_btn = Gtk.Button(label="Add Alias")
        add_first_btn.add_css_class("suggested-action")
        add_first_btn.add_css_class("pill")
        add_first_btn.set_halign(Gtk.Align.CENTER)
        add_first_btn.connect("clicked", self._on_add_clicked)
        self.status_page.set_child(add_first_btn)

        # No results page
        self.no_results_page = Adw.StatusPage()
        self.no_results_page.set_icon_name("system-search-symbolic")
        self.no_results_page.set_title("No Results")
        self.no_results_page.set_description("Try a different search term")

        # CSS
        css = Gtk.CssProvider()
        css.load_from_string("""
            .alias-row subtitle {
                font-family: monospace;
            }
            .section-header {
                font-weight: bold;
                margin-top: 6px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _watch_bashrc(self):
        bashrc = Gio.File.new_for_path(BASHRC_PATH)
        self._monitor = bashrc.monitor_file(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self._monitor.connect("changed", self._on_bashrc_changed)

        history_path = os.path.expanduser("~/.bash_history")
        history_file = Gio.File.new_for_path(history_path)
        self._history_monitor = history_file.monitor_file(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self._history_monitor.connect("changed", self._on_bashrc_changed)

    def _on_bashrc_changed(self, monitor, file, other_file, event_type):
        if self._reload_timeout_id:
            GLib.source_remove(self._reload_timeout_id)
        self._reload_timeout_id = GLib.timeout_add(300, self._reload_debounced)

    def _reload_debounced(self):
        self._reload_timeout_id = None
        self._load()
        return GLib.SOURCE_REMOVE

    def _enter_selection_mode(self, *_):
        self._selection_mode = True
        self._selected.clear()
        self._sync_header()
        self._render()

    def _exit_selection_mode(self, *_):
        self._selection_mode = False
        self._selected.clear()
        self._sync_header()
        self._render()

    def _sync_header(self):
        selecting = self._selection_mode
        self.search_btn.set_visible(not selecting)
        self.add_btn.set_visible(not selecting)
        self.select_btn.set_visible(not selecting)
        self.menu_btn.set_visible(not selecting)
        self.cancel_select_btn.set_visible(selecting)
        self.delete_selected_btn.set_visible(selecting)

    def _on_selection_changed(self, alias_name: str, selected: bool):
        if selected:
            self._selected.add(alias_name)
        else:
            self._selected.discard(alias_name)
        count = len(self._selected)
        self.delete_selected_btn.set_sensitive(count > 0)
        self.delete_selected_btn.set_label(f"Delete ({count})" if count > 0 else "Delete")

    def _on_delete_selected(self, *_):
        count = len(self._selected)
        if not count:
            return
        dialog = Adw.AlertDialog()
        dialog.set_heading(f"Delete {count} alias{'es' if count != 1 else ''}?")
        dialog.set_body("This will remove the selected aliases from your ~/.bashrc.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", f"Delete {count}")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", self._on_bulk_delete_response)
        dialog.present(self)

    def _on_bulk_delete_response(self, dialog, response):
        if response == "delete":
            to_delete = [a for a in self._all_aliases if a.name in self._selected]
            for alias in to_delete:
                delete_alias(alias)
            count = len(to_delete)
            self._exit_selection_mode()
            self.show_toast(f"Deleted {count} alias{'es' if count != 1 else ''}")

    def _load(self):
        self._all_aliases = load_aliases()
        self._render()

    def _render(self):
        # Clear existing content
        while child := self.outer_box.get_first_child():
            self.outer_box.remove(child)

        query = self._search_query.lower().strip()
        aliases = self._all_aliases

        if query:
            aliases = [
                a for a in aliases
                if query in a.name.lower()
                or query in a.command.lower()
                or query in a.comment.lower()
            ]

        if not self._all_aliases:
            self.outer_box.append(self.status_page)
            return

        if not aliases and query:
            self.outer_box.append(self.no_results_page)
            return

        if not query:
            suggestions = get_suggestions(self._all_aliases)
            if suggestions:
                suggestions_group = Adw.PreferencesGroup()
                suggestions_group.set_title("Suggested Aliases")
                suggestions_group.set_description("Commands you run often — click + to create an alias")
                for cmd, count in suggestions:
                    row = Adw.ActionRow()
                    row.set_title(html.escape(cmd))
                    row.set_subtitle(f"Used {count} times")
                    add_btn = Gtk.Button()
                    add_btn.set_icon_name("list-add-symbolic")
                    add_btn.set_tooltip_text("Create alias")
                    add_btn.set_valign(Gtk.Align.CENTER)
                    add_btn.add_css_class("flat")
                    add_btn.connect("clicked", self._on_suggest_clicked, cmd)
                    row.add_suffix(add_btn)
                    suggestions_group.add(row)
                self.outer_box.append(suggestions_group)

        prefs_group = Adw.PreferencesGroup()
        prefs_group.set_title("Your Aliases" if not query else "")
        for alias in aliases:
            prefs_group.add(AliasRow(
                alias,
                selection_mode=self._selection_mode,
                selected=alias.name in self._selected,
                on_selection_changed=self._on_selection_changed,
            ))
        self.outer_box.append(prefs_group)

        # Footer note
        count = len(aliases)
        total = len(self._all_aliases)
        label_text = f"{count} alias{'es' if count != 1 else ''}"
        if query:
            label_text += f" of {total} total"
        footer = Gtk.Label(label=label_text)
        footer.add_css_class("dim-label")
        footer.add_css_class("caption")
        footer.set_margin_top(12)
        self.outer_box.append(footer)

    def _on_search_toggled(self, btn):
        self.search_bar.set_search_mode(btn.get_active())
        if not btn.get_active():
            self.search_entry.set_text("")

    def _on_search_changed(self, entry):
        self._search_query = entry.get_text()
        self._render()

    def _on_suggest_clicked(self, btn, cmd: str):
        prefilled = Alias(name="", command=cmd)
        dialog = AliasDialog(self, prefill=prefilled)
        dialog.connect("closed", self._on_add_dialog_closed)
        dialog.present(self)

    def _on_add_clicked(self, *_):
        dialog = AliasDialog(self)
        dialog.connect("closed", self._on_add_dialog_closed)
        dialog.present(self)

    def _on_add_dialog_closed(self, dialog):
        if dialog.result:
            save_alias(dialog.result)
            self._load()
            self.show_toast(f"Alias '{dialog.result.name}' added")

    def open_edit_dialog(self, alias: Alias):
        dialog = AliasDialog(self, alias=alias)
        dialog.connect("closed", lambda d: self._on_edit_dialog_closed(d, alias))
        dialog.present(self)

    def _on_edit_dialog_closed(self, dialog, old_alias: Alias):
        if dialog.result:
            update_alias(old_alias, dialog.result)
            self._load()
            self.show_toast(f"Alias '{dialog.result.name}' updated")

    def confirm_delete(self, alias: Alias):
        dialog = Adw.AlertDialog()
        dialog.set_heading(f"Delete '{alias.name}'?")
        dialog.set_body(f"This will remove 'alias {alias.name}' from your ~/.bashrc. This cannot be undone.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", lambda d, r: self._on_delete_response(d, r, alias))
        dialog.present(self)

    def _on_delete_response(self, dialog, response, alias):
        if response == "delete":
            delete_alias(alias)
            self._load()
            self.show_toast(f"Alias '{alias.name}' deleted")

    def show_toast(self, message: str):
        toast = Adw.Toast(title=message)
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)


