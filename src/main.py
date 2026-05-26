#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib
try:
    from .window import AliasManagerWindow
    from .alias_store import BASHRC_PATH
except ImportError:
    from window import AliasManagerWindow
    from alias_store import BASHRC_PATH


class AliasManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.aayamrajshakya.aliasmanager",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self.on_activate)

        open_action = Gio.SimpleAction.new("open-bashrc", None)
        open_action.connect("activate", self._on_open_bashrc)
        self.add_action(open_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        self.set_accels_for_action("win.new-alias", ["<Control>n"])
        self.set_accels_for_action("win.toggle-search", ["<Control>f"])

    def on_activate(self, app):
        icons_dir = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'icons')
        )
        if os.path.exists(icons_dir):
            from gi.repository import Gdk
            display = Gdk.Display.get_default()
            if display:
                Gtk.IconTheme.get_for_display(display).add_search_path(icons_dir)
        win = AliasManagerWindow(application=app)
        win.present()

    def _on_open_bashrc(self, action, param):
        Gio.AppInfo.launch_default_for_uri(GLib.filename_to_uri(BASHRC_PATH, None), None)

    def _on_about(self, action, param):
        window = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Alias Manager",
            application_icon="io.github.aayamrajshakya.aliasmanager",
            version="1.0.1",
            comments="Manage your bash aliases visually",
            copyright="© 2026 Aayam Raj Shakya",
            license_type=Gtk.License.GPL_3_0,
            developers=["Aayam Raj Shakya (aayamrajshakya) https://github.com/aayamrajshakya"],
        )
        window.present()


def main():
    GLib.set_application_name("Alias Manager")
    GLib.set_prgname("alias-manager")
    app = AliasManagerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
