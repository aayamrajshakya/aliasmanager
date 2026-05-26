#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
try:
    from .window import AliasManagerWindow
except ImportError:
    from window import AliasManagerWindow


class AliasManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.aliasmanager",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = AliasManagerWindow(application=app)
        win.present()


def main():
    app = AliasManagerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
