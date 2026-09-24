# Ubuntu i915 FRL deep-color patch

`i915-frl-bpc-7.0.patch` is the experimental change used on this mini PC's
Ubuntu `7.0.0-34-generic` kernel. The stock driver caps deep color against
HDMI TMDS even when the CH7218 DP-to-HDMI bridge and TV support FRL. The patch
uses the advertised FRL bandwidth for that bpc selection. With the signed
replacement module installed, the local display reported 3840×2160 at 120 Hz,
12 bpc and DSC, and the TV reported BT.2020 / 12-bit during a 4:4:4 stream.

This is a kernel-version-specific test patch, not a general DKMS module. The
module currently lives at
`/lib/modules/7.0.0-34-generic/updates/moonlight-i915/i915.ko`, leaving the
packaged `kernel/drivers/gpu/drm/i915/i915.ko.zst` intact. The module is signed
with a machine-local MOK key under `/opt/moonlight-i915-test/keys/`; **do not
commit or copy the private signing key**. Secure Boot remains enabled.

The source used for the build was the matching Ubuntu `linux-source-7.0.0`
version `7.0.0-34.34`. After applying the patch to that source tree, the module
was built with:

```sh
make -C /lib/modules/7.0.0-34-generic/build \
  M="$PWD/drivers/gpu/drm/i915" KCFLAGS="-I$PWD/include/trace" -j4 modules
```

After signing with `kmodsign sha512`, install the signed module into the
`updates/moonlight-i915` directory, run `depmod -a 7.0.0-34-generic`, and
reboot. Check `modinfo -n i915` and the `i915_display_info` debugfs file.

To roll back, run `sudo bash rollback-i915-frl.sh` on the mini PC, then reboot.
For a future kernel version, rebuild and revalidate against its matching
source; the current signed binary is only for `7.0.0-34-generic`.
