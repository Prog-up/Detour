project('io.github.prog_up.Detour',
  version: '0.1.0',
  meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=1' ]
)

i18n = import('i18n')
gnome = import('gnome')

subdir('data')
subdir('src')

# Post install hooks
gnome.post_install(
  glib_compile_schemas: false,
  gtk_update_icon_cache: true,
  update_desktop_database: true
)
