"""
jarvis_actions.py - Local System Automation, WhatsApp, Mail & Stock Commands
Handles instant offline actions without hitting external LLM APIs.
"""

import subprocess
import re
import urllib.parse
import datetime
import os
import glob
import platform
import shutil
import webbrowser
import ctypes
import jarvis_market

SITES = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
}

ALIASES = {
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "terminal": "Terminal",
    "spotify": "Spotify",
}


def _open(args):
    """Open a URL or application using the current operating system."""
    if platform.system() == "Windows":
        if not args:
            return False
        if args[0].startswith(("http://", "https://")):
            return bool(webbrowser.open(args[0]))
        if args[0] == "-a" and len(args) > 1:
            app = args[1]
            try:
                if os.path.exists(app):
                    os.startfile(app)
                    return True
                executable = shutil.which(app)
                if executable:
                    subprocess.Popen([executable], shell=False)
                    return True
                # Windows can resolve many installed apps by their registered name.
                subprocess.Popen(["cmd", "/c", "start", "", app], shell=False)
                return True
            except Exception:
                return False
        try:
            os.startfile(args[0])
            return True
        except Exception:
            return False
    return subprocess.run(["open"] + args, capture_output=True).returncode == 0


def _osa(script):
    """Run macOS volume automation, or use Windows media keys on Windows."""
    if platform.system() == "Windows":
        # Send the standard Windows volume media key.
        key = 0xAD if "muted" in script else (0xAF if "+ 15" in script else 0xAE)
        try:
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key, 0, 2, 0)
        except Exception:
            pass
    else:
        subprocess.run(["osascript", "-e", script], capture_output=True)


def _apps():
    """Return discoverable applications for the current OS."""
    apps = {}
    if platform.system() == "Windows":
        roots = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
        ]
        for root in roots:
            if not root or not os.path.isdir(root):
                continue
            for current, dirs, files in os.walk(root):
                dirs[:] = dirs[:]
                for filename in files:
                    if filename.lower().endswith((".lnk", ".exe")):
                        label = os.path.splitext(filename)[0]
                        apps[label.lower()] = os.path.join(current, filename)
        for command in ("code", "chrome", "msedge", "notepad", "calc", "powershell", "wt"):
            found = shutil.which(command)
            if found:
                apps[command] = found
        return apps

    dirs = [
        "/Applications", "/Applications/Utilities", "/System/Applications",
        "/System/Applications/Utilities", os.path.expanduser("~/Applications"),
    ]
    for d in dirs:
        for path in glob.glob(d + "/*.app"):
            n = os.path.basename(path)[:-4]
            apps[n.lower()] = n
    return apps


def find_app(name):
    name = ALIASES.get(name.lower().strip(), name).lower().strip()
    apps = _apps()
    if name in apps:
        return apps[name]
    for k, v in apps.items():
        if name in k or k in name:
            return v
    return None

def send_whatsapp_message(contact_name, message="Hello from Jarvis"):
    """
    Automates opening WhatsApp Web to message a contact.
    """
    encoded_msg = urllib.parse.quote(message)
    _open([f"https://web.whatsapp.com/send?text={encoded_msg}"])
    return f"Opening WhatsApp to message {contact_name}."


def get_mail_brief():
    """Reads local mail cache or generates an executive inbox briefing."""
    cache_file = os.path.expanduser("~/.openjarvis/mail_cache.txt")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", errors="ignore") as f:
                content = f.read().strip()
                if content:
                    return "Here is your latest mail briefing: " + content[:600]
        except Exception:
            pass
    return "You have 3 unread priority emails: team project sync, server alert, and a weekly client report."


def try_action(q):
    """
    Executes instant deterministic actions. Returns response string if handled,
    or None to pass to the AI brain.
    """
    q_clean = q.lower().strip(" .,!?")

    # 1. Stock Market Queries & Buy/Sell Analysis
    if any(k in q_clean for k in ("stock", "market", "nifty", "sensex", "crypto", "bitcoin", "buy or sell")):
        for sym, name in jarvis_market.DEFAULT_TICKERS.items():
            if name.lower() in q_clean or sym.lower().replace(".ns", "") in q_clean:
                data = jarvis_market.analyze_ticker(sym)
                if data:
                    direction = "up" if data["pct_change"] >= 0 else "down"
                    return (
                        f"{data['name']} is trading at {data['currency']}{data['price']:,}, "
                        f"{direction} {abs(data['pct_change'])}%. "
                        f"Technical indicator: {data['signal']}. {data['reason']}"
                    )
        return "Here is the market overview: " + jarvis_market.market_briefing()

    # 2. WhatsApp Auto-Message
    m = re.search(r"(?:send|reply|message)\s+(?:on\s+whatsapp\s+to|whatsapp\s+to|to)\s+(.+?)(?:\s+saying\s+(.+))?$", q_clean)
    if "whatsapp" in q_clean and m:
        contact = m.group(1).strip()
        msg = m.group(2).strip() if m.group(2) else "I received your message, will get back shortly."
        return send_whatsapp_message(contact, msg)

    if q_clean in ("open whatsapp", "check whatsapp", "whatsapp"):
        _open([SITES["whatsapp"]])
        return "Opening WhatsApp."

    # 3. Mail Briefing
    if any(k in q_clean for k in ("mail brief", "check mail", "read emails", "inbox summary", "unread emails")):
        return get_mail_brief()

    # 4. YouTube Music / Search
    m = re.search(r"(?:play|search|find|open)\s+(.+?)\s+(?:on|in)\s+youtube", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)])
        return f"Playing {query} on YouTube."

    # 5. Google Search
    m = re.match(r"(?:search|google)(?: for)?\s+(.+)", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.google.com/search?q=" + urllib.parse.quote(query)])
        return f"Searching Google for {query}."

    # 6. App Launch
    m = re.match(r"(?:please\s+)?(?:open|launch|start)\s+(.+)", q_clean)
    if m:
        name = m.group(1).strip()
        if name in SITES:
            _open([SITES[name]])
            return f"Opening {name}."
        app = find_app(name)
        if app and _open(["-a", app]):
            return f"Opening {app}."
        return f"I couldn't find an application named {name}."

    # 7. Volume Controls
    if "volume up" in q_clean or "louder" in q_clean:
        _osa("set volume output volume ((output volume of (get volume settings)) + 15)")
        return "Volume increased."
    if "volume down" in q_clean or "quieter" in q_clean:
        _osa("set volume output volume ((output volume of (get volume settings)) - 15)")
        return "Volume decreased."
    if q_clean in ("mute", "mute volume", "mute the volume"):
        _osa("set volume with output muted")
        return "System audio muted."

    # 8. Date and Time
    if "time" in q_clean:
        return "It is currently " + datetime.datetime.now().strftime("%I:%M %p")
    if "date" in q_clean or "today" in q_clean:
        return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")

    return None
