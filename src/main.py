import sys
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

try:
    from .window import DetourWindow
except ImportError:
    from window import DetourWindow

class DetourApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.prog_up.Detour")

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            folder_path = None
            if len(sys.argv) > 1:
                arg = sys.argv[-1]
                if os.path.isdir(arg):
                    folder_path = os.path.abspath(arg)
            win = DetourWindow(folder_path=folder_path, application=self)
        win.present()

def main():
    app = DetourApplication()
    # GApplication tries to parse arguments as files by default, which causes errors.
    # We pass only sys.argv[0] to run() and parse sys.argv manually in do_activate.
    return app.run([sys.argv[0]])

if __name__ == '__main__':
    sys.exit(main())
