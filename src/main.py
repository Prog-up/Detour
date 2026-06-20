import sys
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
            win = DetourWindow(application=self)
        win.present()

def main():
    app = DetourApplication()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
