# iOS Deployment — The Mutapa Times (Capacitor)

The iOS app is a Capacitor native shell that loads the live site
(`https://mutapatimes.com`) so news stays fresh, and adds native value
(push notifications, splash, status bar, offline fallback) for App Store
Guideline 4.2 compliance.

- **App name:** The Mutapa Times
- **Bundle ID / appId:** `com.mutapatimes.app`
- **Web content:** live site via `server.url` in `capacitor.config.json`
- **Offline fallback:** `www/index.html`
- **Native bridge:** `js/native-bridge.js` (on the live site; no-op in browsers)

## One-time machine setup
```bash
npm install            # installs Capacitor (node_modules is gitignored)
npx cap sync ios       # copies web assets + plugins into the iOS project
```
Requires Xcode 16+ and an Apple Developer account (you have both).

## Open + run
```bash
npx cap open ios       # opens ios/App in Xcode
```
In Xcode → target **App** → **Signing & Capabilities**:
1. Set **Team** to your Apple Developer team. Bundle ID `com.mutapatimes.app`.
2. Add capability **Push Notifications**.
3. Add capability **Background Modes** → tick **Remote notifications**.
Pick a simulator or a real device and press Run.

## App icon & splash
Generated from `resources/icon.png` (1024, no alpha) and
`resources/splash.png` / `resources/splash-dark.png` (2732). To change the
artwork, replace those files and run:
```bash
npx capacitor-assets generate --ios && npx cap sync ios
```

## Push notifications (APNs)
1. In the Apple Developer portal → **Certificates, IDs & Profiles → Keys** →
   create an **APNs Auth Key (.p8)**. Note the Key ID and your Team ID.
2. Use that key in whatever push backend you choose (e.g. Firebase Cloud
   Messaging, OneSignal, or a custom APNs sender).
3. The app already requests permission and registers on launch via
   `js/native-bridge.js`; wire the `registration` token (logged today) to the
   backend so you can send breaking-news alerts. Payloads with a `data.url`
   deep-link straight into the article.

## App Store Connect
1. Create the app record (Bundle ID `com.mutapatimes.app`, category **News**).
2. **Privacy policy URL:** `https://mutapatimes.com/privacy`.
3. **App Privacy:** declare data collected via the site's ad/analytics stack
   (e.g. Google AdSense, identifiers/usage). Be accurate.
4. Screenshots: 6.7" (1290×2796) and 6.5" required; iPad 12.9" if you ship
   universal. Capture from the running app or a simulator.
5. In Xcode: set **Version** (e.g. 1.0.0) and **Build** (increment each
   upload) → **Product → Archive** → **Distribute App → App Store Connect**.
6. Add to **TestFlight**, test on device, then **Submit for Review**.

## App Store Review 4.2 (minimum functionality)
This is a real publication with deep, frequently-updated content, plus
push notifications, offline handling, native splash/status bar and home-screen
shortcuts. In the review notes, frame it as the official Mutapa Times app and
mention push alerts and offline reading. If a reviewer pushes back on "web
content," lean on the push + offline native features.

## Updating the app
- **Content** updates automatically (the shell loads the live site).
- **Native** changes (icons, plugins, config): `npx cap sync ios`, bump the
  build number in Xcode, archive and upload again.

## What's committed vs generated
- Committed: `capacitor.config.json`, `package.json`, `package-lock.json`,
  `www/`, `resources/`, `ios/` (Xcode project), `js/native-bridge.js`.
- Gitignored: `node_modules/`, iOS build artifacts (`ios/App/build`,
  `App/public`, `DerivedData`, xcuserdata).

---

# Google Play (Android, Capacitor)

The Android app is the same Capacitor shell. It was added with
`npx cap add android` and shares `capacitor.config.json`, `www/`, the M·T
icons/splash and `js/native-bridge.js`.

## One-time machine setup (the part not yet installed here)
1. Install **Android Studio** (includes the Android SDK).
2. Install a **JDK 17+** (Android Studio bundles one; or `brew install --cask zulu17`).
3. `npm install` then `npx cap sync android`.

## Open + run
```bash
npx cap open android      # opens android/ in Android Studio
```
- Let Gradle sync finish. Pick an emulator or a plugged-in device, press **Run ▶**.

## Push notifications (FCM)
Android push uses **Firebase Cloud Messaging**:
1. Create a Firebase project, add an Android app with package
   `com.mutapatimes.app`, download `google-services.json` into
   `android/app/`.
2. The same `js/native-bridge.js` registration flow applies; send via FCM.

## Sign + publish to Google Play
1. Create a **Google Play Developer account** (one-time **$25**).
2. In Android Studio: **Build → Generate Signed Bundle / APK → Android App
   Bundle (.aab)**. Create an upload keystore the first time and **keep it
   safe** (losing it blocks future updates).
3. Recommended: enable **Play App Signing** (Google manages the release key).
4. In **Play Console**: create the app, complete the **Data safety** form
   (declare ad/analytics data), content rating, privacy policy
   `https://mutapatimes.com/privacy`, store listing + screenshots
   (phone + 7"/10" tablet), then upload the `.aab` to **Internal testing**
   first, then **Production**.

## Updating Android
- Content updates automatically (loads the live site).
- Native changes: `npx cap sync android`, bump `versionCode`/`versionName`
  in `android/app/build.gradle`, rebuild the `.aab`, upload.

## What's committed vs generated (Android)
- Committed: the `android/` project, M·T icons/splash.
- Gitignored: `android/build`, `android/app/build`, `.gradle`,
  `local.properties`, keystores.

---

# Push notifications (OneSignal — both stores)

OneSignal is wired in (`onesignal-cordova-plugin`). One service handles APNs
(iOS) and FCM (Android) and gives a dashboard to actually send alerts — which
is the "native value" App Store / Play review wants to see working.

## 1. Create the OneSignal app (free)
1. Sign up at onesignal.com → **New App/Website** → name it "The Mutapa Times".
2. Enable **Apple iOS (APNs)** and **Google Android (FCM)**.
3. Copy the **OneSignal App ID**.

## 2. Paste the App ID
In `js/native-bridge.js`, replace `YOUR_ONESIGNAL_APP_ID` with the real App
ID, then commit/deploy the site. (Push stays off until this is set; the app
falls back to the plain Capacitor registration meanwhile.)

## 3. iOS keys + Xcode
1. In the Apple Developer portal create an **APNs Auth Key (.p8)**; in
   OneSignal's iOS settings upload it with your Key ID + Team ID.
2. In Xcode (target **App** → Signing & Capabilities): add **Push
   Notifications**. (Background mode is already set in `Info.plist`.)
3. Add a **Notification Service Extension**: Xcode → File → New → Target →
   *Notification Service Extension*, name it `OneSignalNotificationServiceExtension`,
   set its team, and paste OneSignal's extension code (their iOS guide gives
   it). This enables confirmed delivery, images and badges.
4. **Push only works on a real device, not the simulator.** Run on your
   iPhone, accept the prompt.

## 4. Android keys
1. Create a **Firebase** project, add an Android app (`com.mutapatimes.app`),
   download `google-services.json` into `android/app/`.
2. In OneSignal's Android settings, connect **FCM v1** (upload the Firebase
   service-account JSON).
3. Build/run in Android Studio, accept the prompt.

## 5. Send + verify
- OneSignal dashboard → **Messages → New Push** → send to "Subscribed Users".
- To deep-link into an article, add **Additional Data** `url` =
  `https://mutapatimes.com/articles/<slug>.html`. The app opens it on tap.

Once a test push arrives on a device, push is functional for store review.
