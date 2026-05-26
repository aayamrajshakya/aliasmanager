# Alias Manager

A native GNOME app to manage your `~/.bashrc` aliases visually.
Built with GTK4 + libadwaita + Python.

## Features

- View all aliases from your `~/.bashrc`, grouped alphabetically
- Add new aliases with name, command, and optional description
- Edit or delete existing aliases
- Search/filter aliases live
- Copy any alias to clipboard
- Automatic `.bashrc` backups before every write
- Looks native in GNOME (dark mode, libadwaita styling)

## Requirements

```bash
# Fedora
sudo dnf install python3-gobject gtk4 libadwaita

# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

## Run without installing (development)

```bash
cd gnome-alias-manager/src
python3 -c "from main import main; main()"
```

## Build & Install with Meson

```bash
meson setup builddir
cd builddir
meson compile
meson install          # installs to /usr/local by default
```

Or with a custom prefix:

```bash
meson setup builddir --prefix=$HOME/.local
cd builddir
meson install
```

Then launch with:
```bash
alias-manager
```

## Open in GNOME Builder

1. Open Builder
2. File → Open → select the `gnome-alias-manager` folder
3. Builder will detect `meson.build` automatically
4. Hit the ▶ Run button

## How it works

- Reads all `alias name='command'` lines from `~/.bashrc` on launch
- Aliases added/edited by this app are tagged with `# [alias-manager]` for tracking
- Unmanaged aliases (added manually) are shown read-only and can be deleted
- A timestamped `.bak` file is created before every write operation

## Notes

- After adding/editing aliases, run `source ~/.bashrc` in your terminal for changes to take effect in existing sessions
- New terminal windows will pick up changes automatically
