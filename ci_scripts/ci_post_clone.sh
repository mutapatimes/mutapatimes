#!/bin/sh
# Xcode Cloud post-clone: this repo does NOT commit node_modules, so the
# Capacitor Swift packages under node_modules/@capacitor/* do not exist until
# we install the JS dependencies. Install Node, install deps, then run a
# Capacitor sync so the iOS project can resolve its local packages.
set -ex

export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "▸ Ensuring Node is available"
if ! command -v node >/dev/null 2>&1; then
  brew install node || brew install node@20 || true
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
node -v
npm -v

echo "▸ Installing npm dependencies at repo root"
cd "$CI_PRIMARY_REPOSITORY_PATH"
npm install --no-audit --no-fund

echo "▸ Capacitor sync (iOS)"
npx cap sync ios

echo "✓ Post-clone setup complete"
