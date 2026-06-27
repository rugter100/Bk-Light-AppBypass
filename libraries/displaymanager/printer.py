import asyncio
import io
from PIL import Image
import json

from .display_session import BleDisplaySession, build_frame


WIDTH = 32
HEIGHT = 32


class LEDGrid:
    def __init__(self, w=WIDTH, h=HEIGHT):
        self.w = w
        self.h = h
        self.grid = [
            [(0, 0, 0) for _ in range(w)]
            for _ in range(h)
        ]
        with open("fonts.json", 'r') as f:
            self.fonts = json.load(f)

    def __getitem__(self, y):
        return self.grid[y]

    def __setitem__(self, y, row):
        self.grid[y] = row

    def clear(self, color=(0, 0, 0)):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = color

    def to_image(self):
        img = Image.new("RGB", (self.w, self.h))
        for y in range(self.h):
            for x in range(self.w):
                img.putpixel((x, y), self.grid[y][x])
        return img

    def to_png_bytes(self):
        buf = io.BytesIO()
        self.to_image().save(buf, format="PNG")
        return buf.getvalue()

    def fill_rect(self, x1, y1, x2, y2, color: [tuple,list]):
        color = tuple(color)
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))

        for y in range(max(0, y1), min(self.h, y2 + 1)):
            for x in range(max(0, x1), min(self.w, x2 + 1)):
                self.grid[y][x] = color

    def draw_text(
            self,
            x,
            y,
            text,
            font_name='3x5',
            color=(255, 255, 255),
            bg_color=(0, 0, 0),
            spacing=1,
            wrap=False
    ):
        font_data = self.fonts[font_name]
        letters = font_data["letters"]
        width, height = font_data["size"]

        cursor_x = x
        cursor_y = y

        for char in text:
            glyph = letters.get(char)

            if glyph is None:
                cursor_x += width + spacing
                continue

            if wrap and cursor_x + width > self.w:
                cursor_x = x
                cursor_y += height + spacing

            if not wrap and cursor_x + width > self.w:
                break

            # draw glyph WITH background fill
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    px = cursor_x + gx
                    py = cursor_y + gy

                    if 0 <= px < self.w and 0 <= py < self.h:
                        if bit == "1":
                            self.grid[py][px] = color
                        else:
                            self.grid[py][px] = bg_color

            cursor_x += width + spacing


class Print:
    def __init__(self, address):
        self.address = address
        self.grid = LEDGrid()
        self._session = None
        self._lock = asyncio.Lock()

    async def connect(self):
        if self._session is None:
            self._session = BleDisplaySession(address=self.address)
            await self._session.__aenter__()

    async def disconnect(self):
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None

    # Good to know, minimum brightness per colour is 22
    async def send_grid(self):
        async with self._lock:
            await self.connect()

            png_bytes = self.grid.to_png_bytes()
            frame = build_frame(png_bytes)

            await self._session.send_frame(frame)