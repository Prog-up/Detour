import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw, GObject

class DetourWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Détour")
        self.set_default_size(1024, 768)
        
        # State
        self.folder_path = None
        self.images = []
        self.filtered_images = []
        self.active_image = None
        self.current_filter = 'all'
        self.current_mode = 'columns'
        self.num_parts = 3
        self.grid_rows = 2
        self.grid_cols = 3
        self.merge_neighbors = False
        self.last_layout = None
        self.updating_ui = False
        self.boxes = []
        
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_child(self.toast_overlay)
        
        # Main Stack
        self.main_stack = Gtk.Stack.new()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.toast_overlay.set_child(self.main_stack)
        
        # 1. Welcome Page (Status Page)
        self.status_page = Adw.StatusPage.new()
        self.status_page.set_title("Welcome to Détour")
        self.status_page.set_description("Open a folder of scanned images to begin.")
        self.status_page.set_icon_name("folder-open-symbolic")
        
        btn_open_init = Gtk.Button.new_with_label("Open Folder…")
        btn_open_init.add_css_class("suggested-action")
        btn_open_init.add_css_class("pill")
        btn_open_init.set_halign(Gtk.Align.CENTER)
        btn_open_init.connect("clicked", self.on_open_folder_clicked)
        self.status_page.set_child(btn_open_init)
        
        self.main_stack.add_named(self.status_page, "welcome")
        
        # 2. Editor Page (NavigationSplitView)
        self.split_view = Adw.NavigationSplitView.new()
        self.main_stack.add_named(self.split_view, "editor")
        
        # Build Sidebar
        sidebar_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        
        sidebar_header = Adw.HeaderBar.new()
        sidebar_header.set_show_end_title_buttons(False)
        # Add open folder button in sidebar
        btn_open_folder = Gtk.Button.new_from_icon_name("folder-open-symbolic")
        btn_open_folder.set_tooltip_text("Open Folder")
        btn_open_folder.connect("clicked", self.on_open_folder_clicked)
        sidebar_header.pack_start(btn_open_folder)
        
        sidebar_box.append(sidebar_header)
        
        # Preferences section in sidebar
        pref_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
        pref_box.set_margin_start(12)
        pref_box.set_margin_end(12)
        pref_box.set_margin_top(12)
        pref_box.set_margin_bottom(12)
        
        # Split Count row (boxed list)
        split_count_list = Gtk.ListBox.new()
        split_count_list.add_css_class("boxed-list")
        
        self.split_count_row = Adw.SpinRow()
        self.split_count_row.set_title("Split Count")
        adj = Gtk.Adjustment.new(3, 1, 100, 1, 1, 0)
        self.split_count_row.set_adjustment(adj)
        self.split_count_row.set_value(3)
        self.split_count_row.connect("changed", self.on_split_count_changed)
        split_count_list.append(self.split_count_row)
        pref_box.append(split_count_list)
        
        # Status filters (linked toggle buttons)
        filter_label = Gtk.Label.new("Filter Status")
        filter_label.set_halign(Gtk.Align.START)
        filter_label.add_css_class("dim-label")
        pref_box.append(filter_label)
        
        filter_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        filter_box.add_css_class("linked")
        filter_box.set_halign(Gtk.Align.CENTER)
        
        self.btn_all = Gtk.ToggleButton.new_with_label("All")
        self.btn_pending = Gtk.ToggleButton.new_with_label("Pending")
        self.btn_done = Gtk.ToggleButton.new_with_label("Done")
        
        self.btn_pending.set_group(self.btn_all)
        self.btn_done.set_group(self.btn_all)
        
        self.btn_all.set_active(True)
        
        self.btn_all.connect("toggled", self.on_filter_changed, 'all')
        self.btn_pending.connect("toggled", self.on_filter_changed, 'pending')
        self.btn_done.connect("toggled", self.on_filter_changed, 'done')
        
        filter_box.append(self.btn_all)
        filter_box.append(self.btn_pending)
        filter_box.append(self.btn_done)
        pref_box.append(filter_box)
        
        sidebar_box.append(pref_box)
        
        # File list Box
        file_list_label = Gtk.Label.new("Images")
        file_list_label.set_halign(Gtk.Align.START)
        file_list_label.set_margin_start(12)
        file_list_label.set_margin_bottom(6)
        file_list_label.add_css_class("dim-label")
        sidebar_box.append(file_list_label)
        
        self.file_list = Gtk.ListBox.new()
        self.file_list.connect("row-selected", self.on_image_selected)
        
        scrolled = Gtk.ScrolledWindow.new()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.file_list)
        sidebar_box.append(scrolled)
        
        sidebar_page = Adw.NavigationPage.new(sidebar_box, "Images")
        self.split_view.set_sidebar(sidebar_page)
        
        # Build Content Page
        content_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        
        content_header = Adw.HeaderBar.new()
        content_box.append(content_header)
        
        # Content header left actions: Prev, Reset
        btn_prev = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        btn_prev.set_tooltip_text("Previous Image (←)")
        btn_prev.connect("clicked", lambda b: self.navigate('prev'))
        content_header.pack_start(btn_prev)
        
        btn_reset = Gtk.Button.new_with_label("Reset")
        btn_reset.set_tooltip_text("Reset Layout (R)")
        btn_reset.connect("clicked", lambda b: self.reset_layout_to_equal())
        content_header.pack_start(btn_reset)
        
        # Content header center mode selector + grid spins
        header_center_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        
        mode_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        mode_box.add_css_class("linked")
        
        self.btn_mode_col = Gtk.ToggleButton.new_with_label("Columns")
        self.btn_mode_row = Gtk.ToggleButton.new_with_label("Rows")
        self.btn_mode_grid = Gtk.ToggleButton.new_with_label("Grid")
        self.btn_mode_free = Gtk.ToggleButton.new_with_label("Freeform")
        
        self.btn_mode_row.set_group(self.btn_mode_col)
        self.btn_mode_grid.set_group(self.btn_mode_col)
        self.btn_mode_free.set_group(self.btn_mode_col)
        
        self.btn_mode_col.set_active(True)
        
        self.btn_mode_col.connect("toggled", self.on_mode_toggled, 'columns')
        self.btn_mode_row.connect("toggled", self.on_mode_toggled, 'rows')
        self.btn_mode_grid.connect("toggled", self.on_mode_toggled, 'grid')
        self.btn_mode_free.connect("toggled", self.on_mode_toggled, 'freeform')
        
        mode_box.append(self.btn_mode_col)
        mode_box.append(self.btn_mode_row)
        mode_box.append(self.btn_mode_grid)
        mode_box.append(self.btn_mode_free)
        header_center_box.append(mode_box)
        
        # Grid config box
        self.grid_config_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        self.grid_config_box.append(Gtk.Label.new("  Grid:"))
        
        self.grid_rows_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.grid_rows_spin.set_value(2)
        self.grid_rows_spin.connect("value-changed", self.on_grid_spin_changed)
        self.grid_config_box.append(self.grid_rows_spin)
        
        self.grid_config_box.append(Gtk.Label.new("×"))
        
        self.grid_cols_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.grid_cols_spin.set_value(3)
        self.grid_cols_spin.connect("value-changed", self.on_grid_spin_changed)
        self.grid_config_box.append(self.grid_cols_spin)
        
        self.grid_config_box.set_visible(False)
        header_center_box.append(self.grid_config_box)
        
        content_header.set_title_widget(header_center_box)
        
        # Content header right actions: Merge Neighbors, Save & Next
        self.btn_merge = Gtk.ToggleButton.new_with_label("Merge Neighbors")
        self.btn_merge.connect("toggled", self.on_merge_toggled)
        content_header.pack_end(self.btn_merge)
        
        btn_save = Gtk.Button.new_with_label("Save & Next")
        btn_save.add_css_class("suggested-action")
        btn_save.set_tooltip_text("Save perspective crops and advance (Space / Enter)")
        btn_save.connect("clicked", lambda b: self.save_current_splits())
        content_header.pack_end(btn_save)
        
        # Drawing Canvas
        from .canvas import DetourCanvas
        self.canvas = DetourCanvas()
        self.canvas.set_vexpand(True)
        self.canvas.set_hexpand(True)
        self.canvas.connect("changed", lambda c: self.save_last_layout())
        content_box.append(self.canvas)
        
        content_page = Adw.NavigationPage.new(content_box, "Canvas")
        self.split_view.set_content(content_page)

    def setup_shortcuts(self):
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

    def on_key_pressed(self, controller, keyval, keycode, state):
        focus = self.get_focus()
        if focus and isinstance(focus, (Gtk.Editable, Gtk.Entry)):
            return False
            
        if keyval in (Gdk.KEY_space, Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.save_current_splits()
            return True
        elif keyval == Gdk.KEY_Left:
            self.navigate('prev')
            return True
        elif keyval == Gdk.KEY_Right:
            self.navigate('next')
            return True
        elif keyval in (Gdk.KEY_r, Gdk.KEY_R):
            self.reset_layout_to_equal()
            return True
        elif keyval in (Gdk.KEY_v, Gdk.KEY_V):
            self.set_mode('columns')
            return True
        elif keyval in (Gdk.KEY_h, Gdk.KEY_H):
            self.set_mode('rows')
            return True
        elif keyval in (Gdk.KEY_g, Gdk.KEY_G):
            self.set_mode('grid')
            return True
        elif keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.set_mode('freeform')
            return True
            
        return False

    def set_mode(self, mode_name):
        self.current_mode = mode_name
        if self.current_mode == 'grid':
            self.num_parts = self.grid_rows * self.grid_cols
        else:
            self.num_parts = int(self.split_count_row.get_value())
        self.reset_layout_to_equal()
        self.sync_mode_buttons()

    def on_open_folder_clicked(self, button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select Working Folder")
        dialog.select_folder(self, None, self.on_folder_selected_cb)

    def on_folder_selected_cb(self, dialog, result):
        try:
            folder_file = dialog.select_folder_finish(result)
            if folder_file:
                path = folder_file.get_path()
                self.load_folder(path)
        except Exception as e:
            print("Folder selection error:", e)

    def load_folder(self, path):
        if not path or not os.path.isdir(path):
            self.show_toast("Selected path is not a valid directory.")
            return
            
        self.folder_path = path
        from .imaging import list_images
        self.images = list_images(path)
        
        if not self.images:
            self.show_toast("No supported images (*.jpg/png/webp) found in folder.")
            self.main_stack.set_visible_child_name("editor")
            self.active_image = None
            self.filtered_images = []
            self.apply_filter()
            self.canvas.set_image(None)
            self.canvas.set_boxes([])
            return
            
        self.main_stack.set_visible_child_name("editor")
        self.apply_filter()
        if self.filtered_images:
            self.select_image(self.filtered_images[0])

    def apply_filter(self):
        self.filtered_images = []
        for img in self.images:
            if self.current_filter == 'all':
                self.filtered_images.append(img)
            elif self.current_filter == 'pending' and img['status'] == 'pending':
                self.filtered_images.append(img)
            elif self.current_filter == 'done' and img['status'] == 'done':
                self.filtered_images.append(img)
                
        self.populate_file_list()

    def populate_file_list(self):
        self.updating_ui = True
        self.file_list.remove_all()
        for img in self.filtered_images:
            row_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
            
            name_label = Gtk.Label.new(img['name'])
            name_label.set_halign(Gtk.Align.START)
            name_label.set_hexpand(True)
            name_label.set_ellipsize(3) # END
            
            size_str = f"{img['width']}×{img['height']}" if img['width'] > 0 else ""
            dim_label = Gtk.Label.new(size_str)
            dim_label.add_css_class("dim-label")
            
            dot = Gtk.Image.new_from_icon_name("media-record-symbolic")
            if img['status'] == 'done':
                dot.add_css_class("success")
            else:
                dot.add_css_class("dim-label")
                
            row_box.append(name_label)
            row_box.append(dim_label)
            row_box.append(dot)
            
            row = Gtk.ListBoxRow.new()
            row.set_child(row_box)
            row.img_data = img
            self.file_list.append(row)
            
        # Reselect active image in list if it is still inside filtered list
        if self.active_image:
            found = False
            for idx in range(len(self.filtered_images)):
                row = self.file_list.get_row_at_index(idx)
                if row and row.img_data['path'] == self.active_image['path']:
                    self.file_list.select_row(row)
                    found = True
                    break
            if not found:
                self.active_image = None
                self.canvas.set_image(None)
                self.canvas.set_boxes([])
                
        self.updating_ui = False

    def on_image_selected(self, list_box, row):
        if self.updating_ui or not row:
            return
        self.select_image(row.img_data)

    def select_image(self, img):
        self.active_image = img
        
        # Load image preview surface
        from .imaging import load_display_surface
        try:
            surface = load_display_surface(img['path'])
            self.canvas.set_image(surface)
        except Exception as e:
            self.show_toast(f"Error loading image: {e}")
            return
            
        # Re-apply or reset layout
        from .models import Point, Quad, apply_neighbors_merge, unmerge
        if self.last_layout and len(self.last_layout['boxes']) == self.num_parts:
            self.current_mode = self.last_layout['mode']
            self.boxes = []
            for b in self.last_layout['boxes']:
                self.boxes.append(Quad(
                    Point(b['tl']['x'], b['tl']['y']),
                    Point(b['tr']['x'], b['tr']['y']),
                    Point(b['br']['x'], b['br']['y']),
                    Point(b['bl']['x'], b['bl']['y'])
                ))
            if self.current_mode == 'grid':
                self.grid_rows = self.last_layout['rows_val']
                self.grid_cols = self.last_layout['cols_val']
                
                self.updating_ui = True
                self.grid_rows_spin.set_value(self.grid_rows)
                self.grid_cols_spin.set_value(self.grid_cols)
                self.updating_ui = False
        else:
            self.current_mode = 'columns'
            self.num_parts = int(self.split_count_row.get_value())
            from .models import make_layout
            self.boxes = make_layout(self.current_mode, self.num_parts, self.grid_rows, self.grid_cols)
            
        if self.merge_neighbors:
            unmerge(self.boxes)
            apply_neighbors_merge(self.current_mode, self.boxes, self.grid_rows, self.grid_cols)
            
        self.canvas.set_boxes(self.boxes)
        self.save_last_layout()
        self.sync_mode_buttons()

        # Update ListBox selection highlight in sync
        self.updating_ui = True
        for idx in range(len(self.filtered_images)):
            row = self.file_list.get_row_at_index(idx)
            if row and row.img_data['path'] == img['path']:
                self.file_list.select_row(row)
                break
        self.updating_ui = False

    def reset_layout_to_equal(self):
        if not self.active_image:
            return
            
        from .models import make_layout, apply_neighbors_merge
        if self.current_mode == 'grid':
            self.num_parts = self.grid_rows * self.grid_cols
            
        self.boxes = make_layout(self.current_mode, self.num_parts, self.grid_rows, self.grid_cols)
        
        if self.merge_neighbors:
            apply_neighbors_merge(self.current_mode, self.boxes, self.grid_rows, self.grid_cols)
            
        self.canvas.set_boxes(self.boxes)
        self.save_last_layout()

    def save_last_layout(self):
        if not self.active_image or not self.boxes:
            return
        self.last_layout = {
            'mode': self.current_mode,
            'boxes': [
                {
                    'tl': {'x': b.tl.x, 'y': b.tl.y},
                    'tr': {'x': b.tr.x, 'y': b.tr.y},
                    'br': {'x': b.br.x, 'y': b.br.y},
                    'bl': {'x': b.bl.x, 'y': b.bl.y}
                } for b in self.boxes
            ],
            'rows_val': self.grid_rows,
            'cols_val': self.grid_cols
        }

    def sync_mode_buttons(self):
        self.updating_ui = True
        self.btn_mode_col.set_active(self.current_mode == 'columns')
        self.btn_mode_row.set_active(self.current_mode == 'rows')
        self.btn_mode_grid.set_active(self.current_mode == 'grid')
        self.btn_mode_free.set_active(self.current_mode == 'freeform')
        self.update_mode_visibility()
        self.btn_merge.set_active(self.merge_neighbors)
        self.updating_ui = False

    def on_split_count_changed(self, spin_row):
        if self.updating_ui:
            return
        self.num_parts = int(spin_row.get_value())
        self.reset_layout_to_equal()

    def on_filter_changed(self, button, filter_type):
        if self.updating_ui:
            return
        if button.get_active():
            self.current_filter = filter_type
            self.apply_filter()

    def on_mode_toggled(self, button, mode_name):
        if self.updating_ui:
            return
        if button.get_active():
            self.set_mode(mode_name)

    def on_grid_spin_changed(self, spin):
        if self.updating_ui:
            return
        self.grid_rows = int(self.grid_rows_spin.get_value())
        self.grid_cols = int(self.grid_cols_spin.get_value())
        self.num_parts = self.grid_rows * self.grid_cols
        self.reset_layout_to_equal()

    def on_merge_toggled(self, button):
        if self.updating_ui:
            return
        self.merge_neighbors = button.get_active()
        from .models import apply_neighbors_merge, unmerge
        if self.merge_neighbors:
            apply_neighbors_merge(self.current_mode, self.boxes, self.grid_rows, self.grid_cols)
        else:
            unmerge(self.boxes)
        self.canvas.set_boxes(self.boxes)
        self.save_last_layout()

    def update_mode_visibility(self):
        self.grid_config_box.set_visible(self.current_mode == 'grid')
        self.split_count_row.set_sensitive(self.current_mode != 'grid')

    def show_toast(self, message):
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)

    def save_current_splits(self):
        if not self.active_image or not self.boxes:
            return
            
        from .imaging import split_image
        try:
            split_image(self.active_image['path'], self.boxes)
            self.show_toast(f"Successfully saved {len(self.boxes)} cropped quads!")
            
            # Re-read status of this image from files
            self.active_image['status'] = 'done'
            
            # Save index we were at
            current_idx = -1
            for i, img in enumerate(self.filtered_images):
                if img['path'] == self.active_image['path']:
                    current_idx = i
                    break
                    
            # Re-apply filters which updates ListBox
            self.apply_filter()
            
            # Select next image if possible
            if current_idx != -1:
                next_img = None
                if current_idx < len(self.filtered_images):
                    next_img = self.filtered_images[current_idx]
                elif len(self.filtered_images) > 0:
                    next_img = self.filtered_images[-1]
                    
                if next_img:
                    self.select_image(next_img)
                else:
                    self.active_image = None
                    self.canvas.set_image(None)
                    self.canvas.set_boxes([])
                    self.show_toast("All items processed or end of list reached!")
        except Exception as e:
            self.show_toast(f"Warp crop failed: {e}")

    def navigate(self, direction):
        if not self.active_image or not self.filtered_images:
            return
            
        current_idx = -1
        for i, img in enumerate(self.filtered_images):
            if img['path'] == self.active_image['path']:
                current_idx = i
                break
                
        if current_idx == -1:
            return
            
        if direction == 'next':
            next_idx = (current_idx + 1) % len(self.filtered_images)
        else:
            next_idx = (current_idx - 1) % len(self.filtered_images)
            
        self.select_image(self.filtered_images[next_idx])
