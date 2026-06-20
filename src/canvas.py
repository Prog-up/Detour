import math
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GObject
import cairo

def point_in_polygon(x, y, poly_pts):
    n = len(poly_pts)
    inside = False
    p1x, p1y = poly_pts[0].x, poly_pts[0].y
    for i in range(n + 1):
        p2x, p2y = poly_pts[i % n].x, poly_pts[i % n].y
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class DetourCanvas(Gtk.DrawingArea):
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.image_surface = None
        self.boxes = []
        self.hovered_point = None
        self.hovered_quad_idx = None
        self.drag_info = None
        
        self.draw_w = 0
        self.draw_h = 0
        self.offset_x = 0
        self.offset_y = 0
        
        self.set_draw_func(self.draw_func)
        
        # Event Controllers
        drag = Gtk.GestureDrag.new()
        drag.connect("drag-begin", self.on_drag_begin)
        drag.connect("drag-update", self.on_drag_update)
        drag.connect("drag-end", self.on_drag_end)
        self.add_controller(drag)
        
        motion = Gtk.EventControllerMotion.new()
        motion.connect("motion", self.on_motion)
        motion.connect("leave", self.on_leave)
        self.add_controller(motion)

    def set_image(self, surface):
        self.image_surface = surface
        self.queue_draw()
        
    def set_boxes(self, boxes):
        self.boxes = boxes
        self.queue_draw()

    def set_cursor_by_name(self, cursor_name):
        display = self.get_display() if self.get_realized() else Gdk.Display.get_default()
        if display and cursor_name:
            cursor = Gdk.Cursor.new_from_name(cursor_name, None)
            self.set_cursor(cursor)
        else:
            self.set_cursor(None)

    def draw_func(self, area, cr, width, height, *user_data):
        # Draw background
        cr.set_source_rgb(0.07, 0.07, 0.08)
        cr.paint()
        
        if not self.image_surface:
            return
            
        img_w = self.image_surface.get_width()
        img_h = self.image_surface.get_height()
        
        scale = min(width / img_w, height / img_h)
        self.draw_w = img_w * scale
        self.draw_h = img_h * scale
        self.offset_x = (width - self.draw_w) / 2
        self.offset_y = (height - self.draw_h) / 2
        
        # Draw image containing object fit contain
        cr.save()
        cr.translate(self.offset_x, self.offset_y)
        cr.scale(scale, scale)
        cr.set_source_surface(self.image_surface, 0, 0)
        cr.paint()
        cr.restore()
        
        # Draw quads
        for idx, box in enumerate(self.boxes):
            p_tl = (self.offset_x + box.tl.x * self.draw_w, self.offset_y + box.tl.y * self.draw_h)
            p_tr = (self.offset_x + box.tr.x * self.draw_w, self.offset_y + box.tr.y * self.draw_h)
            p_br = (self.offset_x + box.br.x * self.draw_w, self.offset_y + box.br.y * self.draw_h)
            p_bl = (self.offset_x + box.bl.x * self.draw_w, self.offset_y + box.bl.y * self.draw_h)
            
            cr.move_to(*p_tl)
            cr.line_to(*p_tr)
            cr.line_to(*p_br)
            cr.line_to(*p_bl)
            cr.close_path()
            
            # Fill with subtle primary color
            if self.hovered_quad_idx == idx:
                cr.set_source_rgba(0.388, 0.4, 0.945, 0.15)
            else:
                cr.set_source_rgba(0.388, 0.4, 0.945, 0.05)
            cr.fill_preserve()
            
            # Stroke
            cr.set_source_rgb(0.388, 0.4, 0.945) # Indigo
            cr.set_line_width(2.0)
            cr.stroke()
            
            # Draw "Selection N" label at centroid
            cx = (box.tl.x + box.tr.x + box.br.x + box.bl.x) / 4
            cy = (box.tl.y + box.tr.y + box.br.y + box.bl.y) / 4
            
            label = f"Selection {idx + 1}"
            cr.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(13.0)
            extents = cr.text_extents(label)
            tx = (self.offset_x + cx * self.draw_w) - extents.x_bearing - extents.width / 2
            ty = (self.offset_y + cy * self.draw_h) - extents.y_bearing - extents.height / 2
            
            # Shadow
            cr.set_source_rgba(0, 0, 0, 0.5)
            cr.move_to(tx, ty + 1)
            cr.show_text(label)
            # Text
            cr.set_source_rgba(1, 1, 1, 0.35)
            cr.move_to(tx, ty)
            cr.show_text(label)
            
        # Draw unique handles
        from models import unique_handles
        handles = unique_handles(self.boxes)
        for handle in handles:
            pt = handle['pt']
            is_hovered = (self.hovered_point is pt)
            radius = 9.0 if is_hovered else 7.0
            hx = self.offset_x + pt.x * self.draw_w
            hy = self.offset_y + pt.y * self.draw_h
            
            cr.save()
            cr.set_source_rgba(0, 0, 0, 0.3)
            cr.arc(hx, hy + 2, radius, 0, 2 * math.pi)
            cr.fill()
            cr.restore()
            
            # White fill
            cr.set_source_rgb(1.0, 1.0, 1.0)
            if is_hovered:
                cr.set_source_rgb(0.024, 0.714, 0.839) # Accent cyan
            cr.arc(hx, hy, radius, 0, 2 * math.pi)
            cr.fill()
            
            # Stroke
            cr.set_source_rgb(0.024, 0.714, 0.839) # Accent cyan
            cr.set_line_width(2.5)
            cr.arc(hx, hy, radius, 0, 2 * math.pi)
            cr.stroke()

    def on_drag_begin(self, gesture, start_x, start_y):
        if not self.image_surface or not self.boxes:
            self.drag_info = None
            return
            
        # Hit test handles first
        from models import unique_handles
        handles = unique_handles(self.boxes)
        for handle in handles:
            pt = handle['pt']
            hx = self.offset_x + pt.x * self.draw_w
            hy = self.offset_y + pt.y * self.draw_h
            if math.sqrt((start_x - hx)**2 + (start_y - hy)**2) <= 12:
                self.drag_info = {
                    'type': 'vertex',
                    'pt': pt,
                    'start_val': (pt.x, pt.y)
                }
                return
                
        # Else hit test polygon interior
        norm_x = (start_x - self.offset_x) / self.draw_w if self.draw_w > 0 else -1
        norm_y = (start_y - self.offset_y) / self.draw_h if self.draw_h > 0 else -1
        
        if 0 <= norm_x <= 1 and 0 <= norm_y <= 1:
            for idx, box in enumerate(self.boxes):
                poly = [box.tl, box.tr, box.br, box.bl]
                if point_in_polygon(norm_x, norm_y, poly):
                    self.drag_info = {
                        'type': 'polygon',
                        'idx': idx,
                        'start_box_vals': {
                            'tl': (box.tl.x, box.tl.y),
                            'tr': (box.tr.x, box.tr.y),
                            'br': (box.br.x, box.br.y),
                            'bl': (box.bl.x, box.bl.y)
                        }
                    }
                    return
                    
        self.drag_info = None

    def on_drag_update(self, gesture, offset_x, offset_y):
        if not self.drag_info or self.draw_w == 0 or self.draw_h == 0:
            return
            
        pct_delta_x = offset_x / self.draw_w
        pct_delta_y = offset_y / self.draw_h
        
        if self.drag_info['type'] == 'vertex':
            pt = self.drag_info['pt']
            start_x_val, start_y_val = self.drag_info['start_val']
            pt.x = max(0.0, min(1.0, start_x_val + pct_delta_x))
            pt.y = max(0.0, min(1.0, start_y_val + pct_delta_y))
            
        elif self.drag_info['type'] == 'polygon':
            idx = self.drag_info['idx']
            start_vals = self.drag_info['start_box_vals']
            target = self.boxes[idx]
            
            xs = [start_vals[v][0] for v in ['tl', 'tr', 'br', 'bl']]
            ys = [start_vals[v][1] for v in ['tl', 'tr', 'br', 'bl']]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            pct_delta_x = max(-min_x, min(1.0 - max_x, pct_delta_x))
            pct_delta_y = max(-min_y, min(1.0 - max_y, pct_delta_y))
            
            for v in ['tl', 'tr', 'br', 'bl']:
                pt = getattr(target, v)
                pt.x = start_vals[v][0] + pct_delta_x
                pt.y = start_vals[v][1] + pct_delta_y
                
        self.queue_draw()

    def on_drag_end(self, gesture, offset_x, offset_y):
        if self.drag_info:
            self.emit('changed')
        self.drag_info = None

    def on_motion(self, controller, x, y):
        if not self.image_surface or not self.boxes:
            return
            
        # Hit test handles
        from models import unique_handles
        handles = unique_handles(self.boxes)
        for handle in handles:
            pt = handle['pt']
            hx = self.offset_x + pt.x * self.draw_w
            hy = self.offset_y + pt.y * self.draw_h
            if math.sqrt((x - hx)**2 + (y - hy)**2) <= 12:
                if self.hovered_point is not pt or self.hovered_quad_idx is not None:
                    self.hovered_point = pt
                    self.hovered_quad_idx = None
                    self.set_cursor_by_name(handle['cursor'])
                    self.queue_draw()
                return
                
        # Hit test polygons
        norm_x = (x - self.offset_x) / self.draw_w if self.draw_w > 0 else -1
        norm_y = (y - self.offset_y) / self.draw_h if self.draw_h > 0 else -1
        
        if 0 <= norm_x <= 1 and 0 <= norm_y <= 1:
            for idx, box in enumerate(self.boxes):
                poly = [box.tl, box.tr, box.br, box.bl]
                if point_in_polygon(norm_x, norm_y, poly):
                    if self.hovered_quad_idx != idx or self.hovered_point is not None:
                        self.hovered_point = None
                        self.hovered_quad_idx = idx
                        self.set_cursor_by_name('move')
                        self.queue_draw()
                    return
                    
        if self.hovered_point is not None or self.hovered_quad_idx is not None:
            self.hovered_point = None
            self.hovered_quad_idx = None
            self.set_cursor_by_name(None)
            self.queue_draw()

    def on_leave(self, controller):
        if self.hovered_point is not None or self.hovered_quad_idx is not None:
            self.hovered_point = None
            self.hovered_quad_idx = None
            self.set_cursor_by_name(None)
            self.queue_draw()
