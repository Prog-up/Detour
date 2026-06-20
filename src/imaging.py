import os
import glob
import math
import hashlib
from PIL import Image, ImageOps
import cairo
from gi.repository import GLib

def get_cache_path(path):
    h = hashlib.md5(path.encode('utf-8')).hexdigest()
    _, ext = os.path.splitext(path)
    cache_dir = os.path.join(GLib.get_user_cache_dir(), 'detour')
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{h}{ext}")

def list_images(folder):
    if not folder or not os.path.isdir(folder):
        return []
    
    images = []
    valid_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    try:
        names = os.listdir(folder)
    except Exception:
        return []

    for name in names:
        base, ext = os.path.splitext(name)
        if ext.lower() not in valid_exts:
            continue
        
        img_path = os.path.join(folder, name)
        if not os.path.isfile(img_path):
            continue
            
        # Check status (done if any splits exist in split subfolder)
        split_dir = os.path.join(folder, 'split')
        is_done = False
        if os.path.isdir(split_dir):
            splits = glob.glob(os.path.join(split_dir, f"{glob.escape(base)}_*"))
            if len(splits) > 0:
                is_done = True
        
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                try:
                    exif = img._getexif()
                    if exif:
                        orientation = exif.get(274)
                        if orientation in [5, 6, 7, 8]:
                            width, height = height, width
                except Exception:
                    pass
        except Exception:
            width, height = 0, 0
            
        images.append({
            'name': name,
            'path': img_path,
            'width': width,
            'height': height,
            'status': 'done' if is_done else 'pending'
        })
        
    return sorted(images, key=lambda x: x['name'].lower())

def load_display_surface(path, max_px=1600):
    cache_path = get_cache_path(path)
    if not os.path.exists(cache_path):
        with Image.open(path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img.thumbnail((max_px, max_px))
            # Save using the format inferred from the extension of the cache_path
            img.save(cache_path)
            
    with Image.open(cache_path) as img:
        img = img.convert("RGBA")
        width, height = img.size
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        data = img.tobytes("raw", "BGRA")
        surface.get_data()[:] = data
        surface.mark_dirty()
        return surface

def split_image(path, quads):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found at {path}")
        
    folder = os.path.dirname(path)
    img_name = os.path.basename(path)
    base_name, ext = os.path.splitext(img_name)
    
    split_dir = os.path.join(folder, 'split')
    os.makedirs(split_dir, exist_ok=True)
    
    saved_paths = []
    with Image.open(path) as img:
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
            
        orig_w, orig_h = img.size
        
        for i, quad in enumerate(quads):
            # quad is assumed to be an object/dict with tl, tr, br, bl having x, y attributes or keys
            # Let's handle both objects with attributes and dicts
            def get_xy(corner_name):
                corner = quad[corner_name] if isinstance(quad, dict) else getattr(quad, corner_name)
                x = corner['x'] if isinstance(corner, dict) else getattr(corner, 'x')
                y = corner['y'] if isinstance(corner, dict) else getattr(corner, 'y')
                return x, y
                
            x_tl, y_tl = get_xy('tl')
            x_tr, y_tr = get_xy('tr')
            x_br, y_br = get_xy('br')
            x_bl, y_bl = get_xy('bl')
            
            x_tl *= orig_w
            y_tl *= orig_h
            x_tr *= orig_w
            y_tr *= orig_h
            x_br *= orig_w
            y_br *= orig_h
            x_bl *= orig_w
            y_bl *= orig_h
            
            w_top = math.sqrt((x_tr - x_tl)**2 + (y_tr - y_tl)**2)
            w_bottom = math.sqrt((x_br - x_bl)**2 + (y_br - y_bl)**2)
            h_left = math.sqrt((x_bl - x_tl)**2 + (y_bl - y_tl)**2)
            h_right = math.sqrt((x_br - x_tr)**2 + (y_br - y_tr)**2)
            
            target_w = max(1, int(max(w_top, w_bottom)))
            target_h = max(1, int(max(h_left, h_right)))
            
            # Pillow QUAD transform format: (x_tl, y_tl, x_bl, y_bl, x_br, y_br, x_tr, y_tr)
            quad_data = (x_tl, y_tl, x_bl, y_bl, x_br, y_br, x_tr, y_tr)
            
            cropped = img.transform((target_w, target_h), Image.QUAD, quad_data, resample=Image.BICUBIC)
            
            out_name = f"{base_name}_{i+1}{ext}"
            out_path = os.path.join(split_dir, out_name)
            cropped.save(out_path, quality=95)
            saved_paths.append(out_path)
            
    return saved_paths
