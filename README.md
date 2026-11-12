# BMS VIP 3.1 — Android Edition

A single-app Android conversion of the BMS VIP toolkit.

## Included modules
1. System/app dashboard
2. DNS lookup
3. Single-host TCP connection test
4. Website status check (HTTP GET)
5. Authorized API GET with optional Bearer token
6. JSON validation and formatting
7. Text utilities
8. Private workspace file manager
9. ZIP workspace backups
10. Activity summary and CSV export
11. App/storage information

Network tools perform user-initiated checks against a single host or endpoint. Use them only on systems you own or are authorized to test. This app does not include exploit, credential theft, stealth, or mass-scanning features.

## Build APK
Requires Android SDK and Gradle 8.9+ with JDK 17. Open this project in Android Studio, or run:

```bash
gradle assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`.

GitHub Actions builds the debug APK on every push to `main` and on manual workflow dispatch. Download it from the workflow run's Artifacts section.
