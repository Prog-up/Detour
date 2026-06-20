pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
pythondir = join_paths(get_option('prefix'), get_option('libdir'), meson.project_name())

python_sources = [
  'main.py',
  'window.py',
  'canvas.py',
  'models.py',
  'imaging.py',
]

install_data(python_sources, install_dir: pythondir)

conf = configuration_data()
conf.set('pythondir', pythondir)

configure_file(
  input: 'detour.in',
  output: 'detour',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)
