class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def to_dict(self):
        return {'x': self.x, 'y': self.y}


class Quad:
    def __init__(self, tl, tr, br, bl):
        self.tl = tl
        self.tr = tr
        self.br = br
        self.bl = bl

    def to_dict(self):
        return {
            'tl': self.tl.to_dict(),
            'tr': self.tr.to_dict(),
            'br': self.br.to_dict(),
            'bl': self.bl.to_dict()
        }


def make_layout(mode, num_parts, grid_r=2, grid_c=3):
    padding = 0.02
    boxes = []

    if mode == 'columns':
        total_padding_width = (num_parts + 1) * padding
        width_per_box = (1.0 - total_padding_width) / num_parts
        for i in range(num_parts):
            x1 = padding + i * (width_per_box + padding)
            x2 = x1 + width_per_box
            y1 = 0.05
            y2 = 0.95
            boxes.append(Quad(
                Point(x1, y1),
                Point(x2, y1),
                Point(x2, y2),
                Point(x1, y2)
            ))
            
    elif mode == 'rows':
        total_padding_height = (num_parts + 1) * padding
        height_per_box = (1.0 - total_padding_height) / num_parts
        for i in range(num_parts):
            x1 = 0.05
            x2 = 0.95
            y1 = padding + i * (height_per_box + padding)
            y2 = y1 + height_per_box
            boxes.append(Quad(
                Point(x1, y1),
                Point(x2, y1),
                Point(x2, y2),
                Point(x1, y2)
            ))
            
    elif mode == 'grid':
        R = grid_r
        C = grid_c
        total_padding_w = (C + 1) * padding
        total_padding_h = (R + 1) * padding
        width_per_box = (1.0 - total_padding_w) / C
        height_per_box = (1.0 - total_padding_h) / R
        
        for r in range(R):
            for c in range(C):
                x1 = padding + c * (width_per_box + padding)
                x2 = x1 + width_per_box
                y1 = padding + r * (height_per_box + padding)
                y2 = y1 + height_per_box
                boxes.append(Quad(
                    Point(x1, y1),
                    Point(x2, y1),
                    Point(x2, y2),
                    Point(x1, y2)
                ))
                
    elif mode == 'freeform':
        total_padding_width = (num_parts + 1) * padding
        width_per_box = (1.0 - total_padding_width) / num_parts
        for i in range(num_parts):
            x1 = padding + i * (width_per_box + padding)
            x2 = x1 + width_per_box
            y1 = 0.1
            y2 = 0.9
            boxes.append(Quad(
                Point(x1, y1),
                Point(x2, y1),
                Point(x2, y2),
                Point(x1, y2)
            ))
            
    return boxes


def apply_neighbors_merge(mode, boxes, grid_r=2, grid_c=3):
    if mode == 'freeform' or not boxes:
        return
        
    num_parts = len(boxes)
    if mode == 'columns':
        for i in range(1, num_parts):
            avgTopX = (boxes[i].tl.x + boxes[i-1].tr.x) / 2
            avgTopY = (boxes[i].tl.y + boxes[i-1].tr.y) / 2
            avgBotX = (boxes[i].bl.x + boxes[i-1].br.x) / 2
            avgBotY = (boxes[i].bl.y + boxes[i-1].br.y) / 2
            
            sharedTop = Point(avgTopX, avgTopY)
            boxes[i-1].tr = sharedTop
            boxes[i].tl = sharedTop
            
            sharedBot = Point(avgBotX, avgBotY)
            boxes[i-1].br = sharedBot
            boxes[i].bl = sharedBot
            
    elif mode == 'rows':
        for i in range(1, num_parts):
            avgLeftX = (boxes[i].tl.x + boxes[i-1].bl.x) / 2
            avgLeftY = (boxes[i].tl.y + boxes[i-1].bl.y) / 2
            avgRightX = (boxes[i].tr.x + boxes[i-1].br.x) / 2
            avgRightY = (boxes[i].tr.y + boxes[i-1].br.y) / 2
            
            sharedLeft = Point(avgLeftX, avgLeftY)
            boxes[i-1].bl = sharedLeft
            boxes[i].tl = sharedLeft
            
            sharedRight = Point(avgRightX, avgRightY)
            boxes[i-1].br = sharedRight
            boxes[i].tr = sharedRight
            
    elif mode == 'grid':
        R = grid_r
        C = grid_c
        gridNodes = [[None for _ in range(C + 1)] for _ in range(R + 1)]
        for r in range(R + 1):
            for c in range(C + 1):
                refs = []
                if r < R and c < C:
                    refs.append((r * C + c, 'tl'))
                if r < R and c > 0:
                    refs.append((r * C + (c - 1), 'tr'))
                if r > 0 and c < C:
                    refs.append(((r - 1) * C + c, 'bl'))
                if r > 0 and c > 0:
                    refs.append(((r - 1) * C + (c - 1), 'br'))
                
                if not refs:
                    continue
                    
                sumX = 0
                sumY = 0
                for idx, corner in refs:
                    pt = getattr(boxes[idx], corner)
                    sumX += pt.x
                    sumY += pt.y
                    
                sharedNode = Point(sumX / len(refs), sumY / len(refs))
                gridNodes[r][c] = sharedNode
                
                for idx, corner in refs:
                    setattr(boxes[idx], corner, sharedNode)


def unmerge(boxes):
    for box in boxes:
        box.tl = Point(box.tl.x, box.tl.y)
        box.tr = Point(box.tr.x, box.tr.y)
        box.br = Point(box.br.x, box.br.y)
        box.bl = Point(box.bl.x, box.bl.y)


def unique_handles(boxes):
    seen = set()
    list_pts = []
    for box in boxes:
        for corner in ['tl', 'tr', 'br', 'bl']:
            pt = getattr(box, corner)
            if id(pt) not in seen:
                seen.add(id(pt))
                cursor = 'nwse-resize' if corner in ('tl', 'br') else 'nesw-resize'
                list_pts.append({
                    'pt': pt,
                    'cursor': cursor
                })
    return list_pts
