#!/bin/sh
# Xcode Cloud post-clone: this repo does NOT commit node_modules or the
# generated ios/App/App/public folder, so install the JS dependencies and run
# a Capacitor sync before Xcode Cloud builds.
set -e

echo "▸ Installing Node"
brew install node

echo "▸ Installing npm dependencies"
cd "$CI_PRIMARY_REPOSITORY_PATH"
npm ci || npm install

echo "▸ Capacitor sync (iOS)"
npx cap sync ios

echo "✓ Post-clone setup complete"
