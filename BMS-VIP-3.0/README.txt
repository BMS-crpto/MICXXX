BMS VIP 3.0 — PROFESSIONAL TERMUX TOOLKIT

INSTALL
  pkg update -y
  pkg install python unzip -y
  cd ~/storage/downloads
  unzip -o BMS-VIP-3.0.zip
  cd BMS-VIP-3.0
  python main.py

No pip packages are required. Python 3.9+ recommended.

FEATURES
  1. Local system dashboard (platform, Python, storage)
  2. Network centre:
       - DNS lookup
       - Single-host TCP connection test
       - One-URL website availability check
  3. Authorized HTTPS API GET tester:
       - Optional custom header
       - Header value hidden during input
       - Secret is not saved
       - Response capped at 1 MB
  4. JSON formatter and validator
  5. Text statistics and case conversion
  6. Workspace file manager (confined to ~/.bms_vip/workspace)
  7. ZIP backup of workspace
  8. Activity analytics and CSV export
  9. Appearance preference
  A. About / privacy notes

DATA LOCATIONS
  ~/.bms_vip/workspace/   Files managed by BMS
  ~/.bms_vip/backups/     Workspace ZIP backups
  ~/.bms_vip/activity.json Local action history
  ~/.bms_vip/settings.json Preferences

SAFETY
  - Network tests run only after you enter a single host or URL.
  - API tester supports HTTPS GET only. Use only APIs you own or are
    authorized to access. Never paste passwords or private tokens into
    chats or screenshots. The API header value is hidden and not stored.
  - File manager cannot access paths outside the BMS workspace.
  - BMS does not scan networks, exploit devices, access private accounts,
    mass-message, ban/unban WhatsApp accounts, or scrape users.
  - No download count or user count is claimed by this package.

TROUBLESHOOTING
  python --version
  python main.py
  If the display looks odd, use a standard Termux font and increase the
  terminal width or rotate the phone to landscape.
