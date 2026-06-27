import asyncio
from PIL import Image
import io

# import your repo
from libraries.displaymanager.display_session import BleDisplaySession, build_frame


WIDTH = 32
HEIGHT = 32


class LEDGrid:
    def __init__(self, w=WIDTH, h=HEIGHT):
        self.w = w
        self.h = h

        # initialize grid
        self.grid = [
            [(0, 0, 0) for _ in range(w)]
            for _ in range(h)
        ]

    def __getitem__(self, y):
        return self.grid[y]

    def __setitem__(self, y, row):
        self.grid[y] = row

    def set_pixel(self, x, y, color):
        self.grid[y][x] = color

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

    def fill_rect(self, x1, y1, x2, y2, color):
        # normalize coordinates (in case user swaps them)
        x_start = min(x1, x2)
        x_end = max(x1, x2)
        y_start = min(y1, y2)
        y_end = max(y1, y2)

        # clamp to grid bounds
        x_start = max(0, x_start)
        y_start = max(0, y_start)
        x_end = min(self.w - 1, x_end)
        y_end = min(self.h - 1, y_end)

        # fill region
        for y in range(y_start, y_end + 1):
            for x in range(x_start, x_end + 1):
                self.grid[y][x] = color


async def send_grid(session, grid: LEDGrid):
    png_bytes = grid.to_png_bytes()
    frame = build_frame(png_bytes)
    await session.send_frame(frame)


# ---------------- DEMO ----------------

async def main(grid):

    async with BleDisplaySession(
        address="D7:9D:E8:F6:EB:5C",   # or set env BK_LIGHT_ADDRESS
        log_notifications=False
    ) as session:
        grid.clear()
        await send_grid(session, grid)


if __name__ == "__main__":
    asyncio.run(main(LEDGrid()))