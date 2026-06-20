# Desktop file
desktop_file = i18n.merge_file(
  input: 'io.github.prog_up.Detour.desktop.in',
  output: 'io.github.prog_up.Detour.desktop',
  type: 'desktop',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('Validate desktop file', desktop_file_validate,
    args: [desktop_file.full_path()]
  )
endif

# Metainfo file
metainfo_file = i18n.merge_file(
  input: 'io.github.prog_up.Detour.metainfo.xml.in',
  output: 'io.github.prog_up.Detour.metainfo.xml',
  type: 'xml',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validate metainfo file', appstreamcli,
    args: ['validate', '--no-net', metainfo_file.full_path()]
  )
endif

# Install icons
install_data('icons/hicolor/scalable/apps/io.github.prog_up.Detour.svg',
  install_dir: join_paths(get_option('datadir'), 'icons/hicolor/scalable/apps')
)

install_data('icons/hicolor/symbolic/apps/io.github.prog_up.Detour-symbolic.svg',
  install_dir: join_paths(get_option('datadir'), 'icons/hicolor/symbolic/apps')
)
