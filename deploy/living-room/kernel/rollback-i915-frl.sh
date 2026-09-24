#!/usr/bin/env bash
set -euo pipefail
release=${1:-$(uname -r)}
module="/lib/modules/${release}/updates/moonlight-i915/i915.ko"
if [[ ! -f "$module" ]]; then
  echo "No Moonlight i915 override at $module"
  exit 0
fi
rm -- "$module"
depmod -a "$release"
echo "Removed Moonlight i915 override for $release. Reboot to load the stock driver."