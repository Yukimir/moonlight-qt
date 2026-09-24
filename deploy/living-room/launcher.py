#!/usr/bin/env python3
"""Console-only Moonlight launcher with WOL, splash, and reconnect."""

import argparse
import array
import fcntl
import json
import mmap
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

CONFIG = Path.home() / ".config/moonlight-vplus/living-room.json"
MOONLIGHT = Path.home() / "apps/moonlight-vplus/source/app/moonlight"
RUNTIME = Path.home() / ".cache/moonlight-vplus"


def log(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}", flush=True)


def load_config():
    with CONFIG.open(encoding="utf-8") as handle:
        config = json.load(handle)
    for key in ("host", "app", "wol_mac", "splash_image"):
        if not config.get(key):
            raise ValueError(f"Missing {key} in {CONFIG}")
    bytes.fromhex(config["wol_mac"].replace(":", "").replace("-", ""))
    return config


def font(size):
    try:
        path = subprocess.check_output(
            ["fc-match", "-f", "%{file}", "sans:lang=zh-cn"], text=True
        ).strip()
        return ImageFont.truetype(path, size)
    except (OSError, subprocess.CalledProcessError):
        return ImageFont.load_default()


def render_splash(config, status):
    source = Path(config["splash_image"]).expanduser()
    with Image.open(source) as original:
        image = original.convert("RGB").resize((3840, 2160), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 1510, 3840, 2160), fill=(3, 7, 14, 112))
    draw.text((165, 1680), config.get("splash_title", ""), font=font(108), fill="white")
    draw.text((170, 1845), config.get("splash_subtitle", ""), font=font(52), fill=(226, 233, 240))
    draw.text((171, 1995), status, font=font(38), fill=(153, 218, 239))
    RUNTIME.mkdir(parents=True, exist_ok=True)
    output = RUNTIME / "splash-rendered.png"
    Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB").save(output)
    return output


def show_splash(config, status):
    path = render_splash(config, status)
    try:
        with open("/dev/fb0", "r+b", buffering=0) as framebuffer:
            # Linux fb_var_screeninfo is 40 32-bit words. The color channel
            # offsets tell Pillow which byte layout this i915 fbdev uses.
            mode = array.array("I", [0] * 40)
            fcntl.ioctl(framebuffer.fileno(), 0x4600, mode, True)
            width, height, virtual_height = mode[0], mode[1], mode[3]
            xoffset, yoffset, bpp = mode[4], mode[5], mode[6]
            red, green, blue = mode[8], mode[11], mode[14]
            if bpp != 32 or green != 8 or (red, blue) not in ((16, 0), (0, 16)):
                raise ValueError(f"Unsupported framebuffer layout: {bpp} bpp, RGB {red}/{green}/{blue}")
            stride = int(Path("/sys/class/graphics/fb0/stride").read_text().strip())
            with Image.open(path) as source:
                image = source.resize((width, height), Image.Resampling.LANCZOS)
                pixels = image.tobytes("raw", "BGRX" if red == 16 else "RGBX")
            with mmap.mmap(framebuffer.fileno(), stride * virtual_height) as memory:
                row_bytes = width * 4
                if stride == row_bytes and xoffset == 0 and yoffset == 0:
                    memory[:len(pixels)] = pixels
                else:
                    for row in range(height):
                        start = (row + yoffset) * stride + xoffset * 4
                        memory[start:start + row_bytes] = pixels[row * row_bytes:(row + 1) * row_bytes]
        log(f"Painted framebuffer: {status}")
    except (OSError, ValueError) as exc:
        log(f"Splash failed: {exc}")


def host_online(config):
    try:
        with socket.create_connection((config["host"], config.get("probe_port", 47984)), timeout=2):
            return True
    except OSError:
        return False


def wake_host(config):
    mac = bytes.fromhex(config["wol_mac"].replace(":", "").replace("-", ""))
    packet = b"\xff" * 6 + mac * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (config.get("wol_broadcast", "255.255.255.255"), 9))
    log(f"Sent WOL to {config['wol_mac']}")


def stream(config):
    env = os.environ.copy()
    env.update({
        "QT_QPA_PLATFORM": "offscreen",
        "SDL_VIDEODRIVER": "kmsdrm",
        "SDL_AUDIODRIVER": "alsa",
        "LIBVA_DRIVER_NAME": "iHD",
        "DRM_FORCE_DIRECT": "1",
        "VULKAN_IS_SLOW": "1",
        "MOONLIGHT_AUTO_REPLACE_APP": "1",
    })
    command = [str(MOONLIGHT), "stream", config["host"], config["app"],
               "--4K", "--fps", "120", "--hdr", "--yuv444",
               "--video-codec", "HEVC", "--video-decoder", "hardware",
               "--bitrate", str(config.get("bitrate_kbps", 180000))]
    log(f"Starting Moonlight {config['app']} at {config['host']}")
    output = (RUNTIME / "stream.log").open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT)
        return process, output
    except OSError:
        output.close()
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    config = load_config()
    if args.render_only:
        print(render_splash(config, "正在连接游戏主机…"))
        return 0
    if args.probe_only:
        online = host_online(config)
        print("online" if online else "offline")
        return 0 if online else 1

    show_splash(config, "正在连接游戏主机…")
    last_wake = 0
    while True:
        config = load_config()  # Host IP/MAC changes take effect without a reboot.
        if not host_online(config):
            if time.monotonic() - last_wake >= config.get("wake_interval_seconds", 30):
                try:
                    wake_host(config)
                except OSError as exc:
                    log(f"WOL failed: {exc}")
                last_wake = time.monotonic()
            time.sleep(config.get("retry_seconds", 5))
            continue

        show_splash(config, "正在启动 Steam 大屏幕…")
        process, output = stream(config)
        result = process.wait()
        output.close()
        log(f"Moonlight exited with code {result}; retrying")
        show_splash(config, "连接中断，正在重试…")
        time.sleep(config.get("retry_seconds", 5))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
