# 🎬 Screenplay Wallpapers  
Automatically turn movie scripts into stunning, daily‑changing wallpapers.  
Supports **multiple monitors**, **macOS automation**, **virtual environments**, and **multiple screenplay URLs**.

<img width="1921" height="1077" alt="image" src="https://github.com/user-attachments/assets/bf808f12-b486-4f06-a3e4-89be26b3cd4f" />

---

# 📝 Overview

This project turns a movie script into a sequence of wallpapers.  
Each day, your wallpaper automatically updates to the **next page** of the screenplay.

It preserves:

- Script formatting  
- Line breaks  
- Structure (INT./EXT., dialogue, action lines)  

…resulting in a clean, beautiful, readable wallpaper designed for creative people and film lovers.

---
# 📌 macOS ONLY — requires System Events + LaunchAgents

# ✨ Features

✔ Convert ANY screenplay into wallpapers  
✔ Automatically download + format scripts  
✔ Generate page-by-page wallpaper images  
✔ Sync wallpaper across **ALL monitors** (macOS Tahoe supported)  
✔ Handles all macOS Spaces/desktops  
✔ Daily automatic wallpaper switching  
✔ Per‑script progress tracking  
✔ Works inside a Python virtual environment  
✔ Black + “screenplay gold” color theme  
✔ Fully customizable resolution, colors, layout  


# 🧰 Requirements

- macOS (Sonoma, Sequoia, or Tahoe recommended)
- Python 3.9+ installed
- Command Line Tools installed (`xcode-select --install`)
- Virtual environment (venv)
  
---
# 🛠 Installation (From Scratch)
## 📥 1. Clone the Repository
```bash
git clone https://github.com/Kaizenick/ScreenPlayWallpapers
cd ScreenPlayWallpapers
```

## 🛠 2. Install Dependencies (Virtual Environment Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 pillow
```

## 🧪 3. Run the Script Manually
```bash
python3 screenplay_wallpaper.py --url https://www.dailyscript.com/scripts/pulp_fiction.html
```
---

If everything is correct:

- The script downloads Pulp Fiction  
- Processes + cleans the text  
- Generates wallpapers in `wallpapers_pulp_fiction/`  
- Sets today’s wallpaper across both monitors  

At this stage, the program is fully working manually.

---

# 🔧 How the Script Works

### 1. **Downloads Screenplay**
Extracts text from the `<pre>` tag (DailyScript's format).

### 2. **Cleans formatting**
Removes:
- Non-breaking spaces  
- Tabs  
- Invisible control characters  

### 3. **Splits into pages**
Based on `DEFAULT_WORDS_PER_PAGE`.

### 4. **Generates wallpapers**
Uses Pillow to render:
- Black background  
- Screenplay-gold text  
- Left-aligned column  
- Vertically centered  

### 5. **Tracks reading progress**
Creates `<slug>_meta.json` storing start date.

### 6. **Determines today’s page**
`(today - start_date) % number_of_pages`.

### 7. **Sets wallpaper**
Fixes macOS “span displays” setting and applies wallpaper to ALL desktops.

---

# 🎥 Running the Script Manually

To run any script:

```bash
python3 screenplay_wallpaper.py --url <script_url>
```

Example:

```bash
python3 screenplay_wallpaper.py --url https://www.dailyscript.com/scripts/The_Godfather.html
```

---

# ⏱ Setting Up Daily Automation (macOS Service)

macOS uses **LaunchAgents** to run scripts automatically.

---

## **1. Create the LaunchAgent plist**

Run:

```bash
nano ~/Library/LaunchAgents/com.screenplay.pulpfiction.plist
```

Paste:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.screenplay.pulpfiction</string>

    <key>ProgramArguments</key>
    <array>
        <!-- Virtual environment python -->
        <string>/path/to/ScreenPlayWallpapers/venv/bin/python3</string>

        <!-- Script -->
        <string>/path/to/ScreenPlayWallpapers/screenplay_wallpaper.py</string>

        <!-- Script arguments -->
        <string>--url</string>
        <string>https://www.dailyscript.com/scripts/pulp_fiction.html</string>
    </array>

    <!-- Run daily at 09:00 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/screenplay_pulpfiction.out</string>

    <key>StandardErrorPath</key>
    <string>/tmp/screenplay_pulpfiction.err</string>
</dict>
</plist>
```

**IMPORTANT:**  
Replace:

```
/path/to/ScreenPlayWallpapers
```

with your real path:

```
/Users/<yourname>/MyStuff/ScreenPlayWallpapers
```

---

## **2. Load the service**

```bash
launchctl unload ~/Library/LaunchAgents/com.screenplay.pulpfiction.plist 2>/dev/null || true
launchctl load  ~/Library/LaunchAgents/com.screenplay.pulpfiction.plist
```

You should see your wallpaper change immediately (RunAtLoad = true).

---

## **3. Verify logs**

```bash
cat /tmp/screenplay_pulpfiction.out
cat /tmp/screenplay_pulpfiction.err
```

---

# 📊 Checking Service Status

### Is the service loaded?

```bash
launchctl list | grep com.screenplay.pulpfiction
```

### Force-run immediately

```bash
launchctl kickstart -k GUI/$(id -u)/com.screenplay.pulpfiction
```

### Full detailed status

```bash
launchctl print GUI/$(id -u)/com.screenplay.pulpfiction
```

---

# 🎨 Customizing Wallpapers

Inside `screenplay_wallpaper.py`, edit:

### Background color

```python
BG_COLOR = (0, 0, 0)
```

### Text color

```python
TEXT_COLOR = (232, 217, 168)  # #E8D9A8
```

### Resolution

```python
WIDTH, HEIGHT = 1920, 1080
```

### Words per page

```python
DEFAULT_WORDS_PER_PAGE = 900
```

---

# 🎬 Adding More Movies

Create a new LaunchAgent:

Example:

```
~/Library/LaunchAgents/com.screenplay.godfather.plist
```

Just change:

```xml
<string>--url</string>
<string>https://www.dailyscript.com/scripts/The_Godfather.html</string>
```

Each script keeps its own:

- wallpapers  
- metadata  
- rotation schedule  

---

# 🛠 Troubleshooting

### ❌ Wallpaper only changes on one monitor
Solution:  
macOS auto-disables display spanning.  
Script forces:

```bash
defaults -currentHost write com.apple.spaces spans-displays -bool true
killall Dock
```

### ❌ “ModuleNotFoundError: requests”
Use venv python inside plist:

```
/path/to/ScreenPlayWallpapers/venv/bin/python3
```

### ❌ Service not running
Check:

```bash
launchctl list | grep screenplay
```

---

# 🚀 Future Enhancements

- Page N on monitor 1, Page N+1 on monitor 2  
- Fade transitions  
- GUI menu bar app  
- Script-of-the-week auto rotation  
- Support for .fdx (Final Draft)  
- CLI installer  

---

# 📜 License

Free for personal use. Modify and extend as you like.

---

Enjoy your cinematic desktop experience. 🎞✨
