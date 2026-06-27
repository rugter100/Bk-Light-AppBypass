import asyncio
from libraries.displaymanager.printer import Print

async def main():
    display = Print("D7:9D:E8:F6:EB:5C")

    display.grid.clear()

    display.grid.fill_rect(10,10,21,21, (0,0,255))
    display.grid.draw_text(0, 0, "fyygabhsfgdsjgfdgjdfhgj", '3x5', color=(255, 0, 0), wrap=True)
    await display.send_grid()

    await asyncio.sleep(5)

    await display.disconnect()


asyncio.run(main())