import asyncio
import yaml
import io
import json
from .printer import Print

PANEL_W = 32
PANEL_H = 32


class VirtualGrid:
    def __init__(self, manager, group_map, w=None, h=None):
        self.manager = manager
        self.group_map = group_map

        # virtual dimensions (auto-calculated from group)
        if w is None or h is None:
            xs = [c[0] for c in group_map.keys()]
            ys = [c[1] for c in group_map.keys()]
            self.w = (max(xs) + 1) * PANEL_W
            self.h = (max(ys) + 1) * PANEL_H
        else:
            self.w = w
            self.h = h

        # internal buffer (same structure as LEDGrid)
        self.grid = [
            [(0, 0, 0) for _ in range(self.w)]
            for _ in range(self.h)
        ]
        with open("fonts.json", 'r') as f:
            self.fonts = json.load(f)

    # =====================================================
    # PIXEL ACCESS (MATCH LEDGrid EXACTLY)
    # =====================================================
    def __getitem__(self, y):
        return self.grid[y]

    def __setitem__(self, y, row):
        self.grid[y] = row

    # =====================================================
    # CORE PIXEL SETTER (ROUTES TO PANELS)
    # =====================================================
    def set_pixel(self, x, y, color):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return

        self.grid[y][x] = color

        panel_x = x // PANEL_W
        panel_y = y // PANEL_H

        local_x = x % PANEL_W
        local_y = y % PANEL_H

        panel_id = self.group_map.get((panel_x, panel_y))
        if panel_id is None:
            return

        self.manager.displays[panel_id].grid[local_y][local_x] = color

    # =====================================================
    # CLEAR (MATCH LEDGrid)
    # =====================================================
    def clear(self, color=(0, 0, 0)):
        for y in range(self.h):
            for x in range(self.w):
                self.set_pixel(x, y, color)

    # =====================================================
    # FILL RECT (MATCH LEDGrid)
    # =====================================================
    def fill_rect(self, x1, y1, x2, y2, color):
        color = tuple(color)
        x_start = min(x1, x2)
        x_end = max(x1, x2)
        y_start = min(y1, y2)
        y_end = max(y1, y2)

        x_start = max(0, x_start)
        y_start = max(0, y_start)
        x_end = min(self.w - 1, x_end)
        y_end = min(self.h - 1, y_end)

        for y in range(y_start, y_end + 1):
            for x in range(x_start, x_end + 1):
                self.set_pixel(x, y, color)

    def draw_text(
            self,
            x,
            y,
            text,
            font_name='3x5',
            color=(255, 255, 255),
            spacing=1,
            wrap=False,
            background=None
    ):
        font_data = self.fonts[font_name]
        letters = font_data["letters"]
        width, height = font_data["size"]

        cursor_x = x
        cursor_y = y

        for char in text:
            glyph = letters.get(char)

            # unknown char → treat as space
            if glyph is None:
                cursor_x += width + spacing
                continue

            # wrap logic
            if wrap and cursor_x + width > self.w:
                cursor_x = x
                cursor_y += height + spacing

            if not wrap and cursor_x + width > self.w:
                break

            # draw glyph
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    px = cursor_x + gx
                    py = cursor_y + gy

                    if 0 <= px < self.w and 0 <= py < self.h:
                        if bit == "1":
                            self.set_pixel(px, py, color)
                        elif background is not None:
                            self.set_pixel(px, py, background)

            cursor_x += width + spacing
"""
    # =====================================================
    # IMAGE EXPORT (MATCH LEDGrid) Probably not needed?
    # =====================================================
    def to_image(self):
        img = Image.new("RGB", (self.w, self.h))
        for y in range(self.h):
            for x in range(self.w):
                img.putpixel((x, y), self.grid[y][x])
        return img

    def to_png_bytes(self):
        buf = io.BytesIO()
        self.to_image().save(buf, format="PNG")
        return buf.getvalue()"""


class GroupHandle:
    def __init__(self, manager, group_map):
        self.manager = manager
        self.group_map = group_map
        self.grid = VirtualGrid(manager, group_map)

    async def send_grid(self):
        await self.manager.send_group_by_map(self.group_map)


class DisplayManager:
    def __init__(self, config_path="config.yml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.displays = {}
        self.groups = {}
        self.group_handles = {}

        for panel_id, address in config["panels"].items():
            self.displays[int(panel_id)] = Print(address)
            self.displays[int(panel_id)].connect()

    def __getitem__(self, key):
        try:
            key = int(key)
        except (TypeError, ValueError):
            pass

        if isinstance(key, int):
            return self.displays[key]

        if isinstance(key, str):
            if key not in self.group_handles:
                raise KeyError(f"Group '{key}' does not exist")
            return self.group_handles[key]

        raise TypeError("Key must be int (panel) or str (group)")

    @property
    def group(self):
        return self.group_handles

    def panels(self, ids):
        """Return list of Print objects for given IDs"""
        return [self.displays[i] for i in ids]

    async def send(self, key):
        try:
            key = int(key)
        except (TypeError, ValueError):
            pass

        if isinstance(key, int):
            await self.displays[key].send_grid()

        elif isinstance(key, str):
            if key in self.group_handles:
                group = self.groups[key]
                await asyncio.gather(*(self.displays[i].send_grid() for i in group.values()))
                return

            raise KeyError(f"Unknown group '{key}'")

        elif isinstance(key, list):
            await asyncio.gather(
                *(self.displays[i].send_grid() for i in key)
            )

    async def send_group_by_map(self, group_map):
        await asyncio.gather(*(self.displays[i].send_grid() for i in group_map.values()))

    def get_group(self, name):
        return [self.displays[i] for i in self.groups[name].values()]

    def create_group(self, name, mapping: dict):
        # mapping: {(x,y): panel_id}
        # (gx, gy): panel_id

        # ---- 1. validate panels exist
        for panel_id in mapping.values():
            if panel_id not in self.displays:
                raise ValueError(f"Panel {panel_id} does not exist")

        # ---- 2. extract coordinates
        coords = list(mapping.keys())
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # ---- 3. enforce rectangle (NO holes allowed)
        expected = set(
            (x, y)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
        )

        if set(coords) != expected:
            missing = expected - set(coords)
            raise ValueError(
                f"Group '{name}' is not a complete rectangle. Missing: {missing}"
            )

        self.groups[name] = mapping

        self.group_handles[name] = GroupHandle(self, mapping)

    def get_status(self, key):
        try:
            key = int(key)
        except (TypeError, ValueError):
            pass

        if isinstance(key, int):
            return self.displays[key].connection_status()

        elif isinstance(key, str):
            if key in self.group_handles:
                group = self.groups[key]
                return asyncio.gather(*(self.displays[i].connection_status() for i in group.values()))


            raise KeyError(f"Unknown group '{key}'")