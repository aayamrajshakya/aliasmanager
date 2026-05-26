project('alias-manager',
  version: '1.0.0',
  meson_version: '>= 0.62.0',
)

python = import('python').find_installation('python3')
gnome   = import('gnome')
i18n    = import('i18n')

# App metadata
app_id = 'com.github.aliasmanager'

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
  'data/com.github.aliasmanager.desktop',
  install_dir: get_option('datadir') / 'applications',
)

# Install app icon
install_data(
  'data/icons/hicolor/scalable/apps/com.github.aliasmanager.svg',
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
