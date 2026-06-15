#!/bin/sh
# Xcode Cloud pre-build (next to the Xcode project). Stamp the build number
# from the Xcode Cloud build number so every TestFlight/App Store upload is
# unique and increasing. CFBundleVersion is $(CURRENT_PROJECT_VERSION).
set -ex

[ -n "$CI_BUILD_NUMBER" ] || { echo "No CI_BUILD_NUMBER; leaving build number as-is"; exit 0; }

cd "$CI_PRIMARY_REPOSITORY_PATH/ios/App"
agvtool new-version -all "$CI_BUILD_NUMBER"
echo "✓ Build number set to $CI_BUILD_NUMBER"
