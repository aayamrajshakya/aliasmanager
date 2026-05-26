project('alias-manager',
  version: '1.0.0',
  meson_version: '>= 0.62.0',
)

python = import('python').find_installation('python3')
gnome  = import('gnome')

# App metadata
app_id = 'io.github.aayamrajshakya.aliasmanager'

# Install Python sources
python.install_sources(
  'src/__init__.py',
  'src/main.py',
  'src/window.py',
  'src/alias_store.py',
  'src/alias_dialog.py',
  subdir: 'alias_manager',
)

# Install .desktop file
install_data(
  'data/io.github.aayamrajshakya.aliasmanager.desktop',
  install_dir: get_option('datadir') / 'applications',
)

# Install metainfo
install_data(
  'data/io.github.aayamrajshakya.aliasmanager.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo',
)

# Install app icon
install_data(
  'data/icons/hicolor/scalable/apps/io.github.aayamrajshakya.aliasmanager.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
)

# Install and configure the launcher script
conf = configuration_data()
conf.set('PYTHON', python.full_path())
conf.set('pkgdatadir', get_option('prefix') / get_option('datadir') / 'alias_manager')
conf.set('localedir', get_option('prefix') / get_option('localedir'))

configure_file(
  input: 'alias-manager.in',
  output: 'alias-manager',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

gnome.post_install(
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
