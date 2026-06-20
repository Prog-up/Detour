import unittest
import os
import shutil
import tempfile
import cairo
from PIL import Image

# Add src directory to system path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Point, Quad, make_layout, apply_neighbors_merge, unmerge, unique_handles
from imaging import list_images, load_display_surface, split_image

class TestModels(unittest.TestCase):
    def test_layout_generation(self):
        # Columns
        boxes = make_layout('columns', 3)
        self.assertEqual(len(boxes), 3)
        self.assertAlmostEqual(boxes[0].tl.y, 0.05)
        self.assertAlmostEqual(boxes[0].bl.y, 0.95)
        
        # Rows
        boxes = make_layout('rows', 4)
        self.assertEqual(len(boxes), 4)
        
        # Grid
        boxes = make_layout('grid', 6, grid_r=2, grid_c=3)
        self.assertEqual(len(boxes), 6)
        
        # Freeform
        boxes = make_layout('freeform', 2)
        self.assertEqual(len(boxes), 2)

    def test_merge_neighbors(self):
        boxes = make_layout('columns', 3)
        
        # Verify handles are initially independent
        self.assertNotEqual(id(boxes[0].tr), id(boxes[1].tl))
        
        # Apply merge
        apply_neighbors_merge('columns', boxes)
        
        # Now adjacent corners should point to the exact same mutable Point object
        self.assertEqual(id(boxes[0].tr), id(boxes[1].tl))
        self.assertEqual(id(boxes[0].br), id(boxes[1].bl))
        
        # Checking unique handles count
        handles = unique_handles(boxes)
        self.assertEqual(len(handles), 8) # 12 initial corners, 4 merged = 8 unique
        
        # Verify unmerge restores independence
        unmerge(boxes)
        self.assertNotEqual(id(boxes[0].tr), id(boxes[1].tl))
        self.assertNotEqual(id(boxes[0].br), id(boxes[1].bl))

class TestImaging(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.img_path = os.path.join(self.test_dir, "test_scan.png")
        Image.new('RGB', (100, 200), color='blue').save(self.img_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_images(self):
        images = list_images(self.test_dir)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['name'], 'test_scan.png')
        self.assertEqual(images[0]['width'], 100)
        self.assertEqual(images[0]['height'], 200)
        self.assertEqual(images[0]['status'], 'pending')
        
        # Mark as done
        split_dir = os.path.join(self.test_dir, 'split')
        os.makedirs(split_dir)
        open(os.path.join(split_dir, 'test_scan_1.png'), 'w').close()
        
        images = list_images(self.test_dir)
        self.assertEqual(images[0]['status'], 'done')

    def test_load_display_surface(self):
        surface = load_display_surface(self.img_path, max_px=50)
        self.assertIsInstance(surface, cairo.ImageSurface)
        self.assertTrue(surface.get_width() <= 50)
        self.assertTrue(surface.get_height() <= 50)

    def test_split_image(self):
        # Define a quad selection spanning the whole image
        quad = Quad(
            Point(0.0, 0.0), # tl
            Point(1.0, 0.0), # tr
            Point(1.0, 1.0), # br
            Point(0.0, 1.0)  # bl
        )
        saved = split_image(self.img_path, [quad])
        self.assertEqual(len(saved), 1)
        self.assertTrue(os.path.exists(saved[0]))
        
        # Verify the dimensions match original
        with Image.open(saved[0]) as out:
            self.assertEqual(out.size, (100, 200))

if __name__ == '__main__':
    unittest.main()
