import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import List
from bleak import BleakScanner
from PIL import Image, ImageOps

from .display_session import BleDisplaySession

PREFIXES = ("LED_BLE_", "BK_LIGHT", "BJ_LED")

status = {}

def build_logo_png() -> bytes:
    asset_path = Path(__file__).resolve().parents[1] / "assets" / "test_pattern_32x32.png"
    image = Image.open(asset_path).convert("RGB")
    fitted = ImageOps.fit(image, (32, 32), method=Image.Resampling.LANCZOS)
    buffer = BytesIO()
    fitted.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


async def scan_devices(timeout: float = 8.0) -> List:
    devices = await BleakScanner.discover(timeout=timeout)
    compatible = []
    seen = set()
    for device in devices:
        name = device.name or ""
        if any(name.startswith(prefix) for prefix in PREFIXES):
            if device.address not in seen:
                seen.add(device.address)
                compatible.append(device)
    return compatible


async def main() -> list[str]:
    print("Scanning for BK-Light 32x32 displays...")
    devices = await scan_devices()
    if not devices:
        return []
    print("Compatible devices:")
    adress_list = []
    for index, device in enumerate(devices, start=1):
        print(f"{index}. {device.name} {device.address}")
        print(f"Connecting to {device.name} {device.address}")
        try:
            async with BleDisplaySession(device.address) as session:
                png_bytes = build_logo_png()
                await session.send_png(png_bytes)
                adress_list.append(device.address)
            print("Logo sent.")
        except Exception as error:
            print("ERROR", str(error))
    return adress_list

