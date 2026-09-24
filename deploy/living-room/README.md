# Living-room Moonlight deployment

This directory contains the boot and connection glue for an Ubuntu Server
Moonlight terminal. It uses the patched `app/moonlight` binary in this fork.

- `config.json` controls the Sunshine address, Steam Big Picture app name,
  wired WOL MAC, 180 Mbps stream, and editable splash text.
- `splash.png` is a replaceable 3840×2160 image. `set-splash.sh` installs it for
  both Plymouth boot and the connection screen, then refreshes the initramfs.
- `launcher.py` writes the connection image directly to i915's framebuffer,
  sends WOL while Sunshine is unavailable, and reconnects after a dropped session.
- `moonlight-console` is run by tty1's autologin shell.

The 4:4:4 DRM renderer requires `QT_QPA_PLATFORM=offscreen`, so a normal QML
loading page cannot share the display with the streaming renderer. Writing
the image to fbdev avoids a second long-running process taking DRM master;
the framebuffer keeps the image in place until video frames take over.

The installed tty1 login runs `/home/ubuntu/bin/moonlight-console` from
`~/.profile`. The getty has `--autologin ubuntu`, and `.hushlogin` suppresses
the login banner. The active Plymouth theme is `plymouth/moonlight.plymouth`
with `quiet splash` on the kernel command line. The same `splash.png` is
installed into the theme and `~/.local/share/moonlight-vplus/`.

Runtime packages: `python3-pil`, `fonts-noto-cjk`, and `plymouth-themes`.
The tty1 user needs access to `/dev/fb0` and `/dev/dri` (on Ubuntu, membership
in the `video` and `render` groups).

To replace the image, copy any 3840×2160 PNG to the mini PC and run
`~/bin/set-moonlight-splash /path/to/image.png`. The command refreshes the
boot initramfs. Edit `~/.config/moonlight-vplus/living-room.json` to change
the title, subtitle, Steam app name, address, and wired WOL MAC.

Sunshine Foundation on the Windows host uses `display_device_prep =
ensure_primary` and `output_name = ZakoHDR`. This activates the virtual
display as primary for the stream and restores the physical desktop when
the session ends.

On the target mini PC, edit `~/.config/moonlight-vplus/living-room.json` when
the 5090 receives its wired IP. Set `host` to the new IP and `wol_mac` to the
wired adapter's MAC. The launcher reloads the file before each reconnect.

DS5: hold Options for ~0.75 s to toggle Moonlight's built-in mouse mode.
Either stick moves the cursor; Cross is left click, Circle right click,
D-pad scrolls. In mouse mode, Triangle sends Alt+Tab to Windows.
