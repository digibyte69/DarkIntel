import os
import sys
import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

CONFIG_FILE = os.path.expanduser("~/.darkintel_config")

# ANSI Color Palette
R = '\033[1;31m'
G = '\033[1;32m'
C = '\033[1;36m'
Y = '\033[1;33m'
M = '\033[1;35m'
W = '\033[1;37m'
RESET = '\033[0m'

def clear_screen():
    os.system("clear")

def load_api_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return None

def save_api_key(key):
    with open(CONFIG_FILE, "w") as f:
        f.write(key.strip())

def banner():
    art = f"""{R}
    ██████╗  █████╗ ██████╗ ██╗  ██╗██╗███╗   ██╗████████╗███████╗██╗     
    ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██║████╗  ██║╚══██╔══╝██╔════╝██║     
    ██║  ██║███████║██████╔╝█████╔╝ ██║██╔██╗ ██║   ██║   █████╗  ██║     
    ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║██║╚██╗██║   ██║   ██╔══╝  ██║     
    ██████╔╝██║  ██║██║  ██║██║  ██╗██║██║ ╚████║   ██║   ███████╗███████╗
    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝{RESET}
    {C}┌────────────────────────────────────────────────────────────────────┐
    │  {W}Defensive OSINT Engine & Digital Footprint Reconnaissance{C}         │
    │  {Y}Author: @digibyte69{C}  |  {M}Build: v2.1-PRO{C}  |  {G}Platform: Termux / Linux{C}   │
    └────────────────────────────────────────────────────────────────────┘{RESET}
    """
    print(art)

def live_telecom_lookup(cleaned_number, api_key):
    url = f"http://apilayer.net/api/validate?access_key={api_key}&number={cleaned_number}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("valid"):
                return {
                    "valid": True,
                    "carrier": data.get("carrier") or "Unknown / Virtual",
                    "line_type": (data.get("line_type") or "Unknown").upper(),
                    "location": data.get("location") or "Unknown",
                    "country": data.get("country_name") or "Unknown"
                }
    except Exception as e:
        return {"error": str(e)}
    return None

def scan_phone(target, api_key):
    print(f"\n{Y}[*] Probing Carrier Network: {target}{RESET}")
    print(f"{C}{'─'*68}{RESET}")
    try:
        parsed = phonenumbers.parse(target, "US" if not target.startswith("+") else None)
        if not phonenumbers.is_valid_number(parsed):
            print(f"{R}[!] Result: Invalid phone number structure.{RESET}")
            return
    except Exception as e:
        print(f"{R}[!] Parsing failure: {e}{RESET}")
        return

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    region = geocoder.description_for_number(parsed, "en") or "Unknown"
    tz = ", ".join(timezone.time_zones_for_number(parsed))
    default_carr = carrier.name_for_number(parsed, "en") or "Unknown / Virtual Switch"

    print(f"{G}[+] International Format :{RESET} {intl}")
    print(f"{G}[+] Global E.164 Identity:{RESET} {e164}")
    print(f"{G}[+] Telecom Regional Hub :{RESET} {region}")
    print(f"{G}[+] Registered Timezone  :{RESET} {tz}")

    if api_key:
        print(f"\n{Y}[*] Interrogating live telecom switchboards...{RESET}")
        live = live_telecom_lookup(e164, api_key)
        if live and not live.get("error"):
            print(f"{G}[+] Verified Carrier     :{RESET} {live['carrier']}")
            print(f"{G}[+] Line Architecture    :{RESET} {live['line_type']}")
            print(f"{G}[+] Hardware Exchange    :{RESET} {live['location']}, {live['country']}")
        else:
            print(f"{Y}[!] Offline Carrier Link :{RESET} {default_carr}")
    else:
        print(f"{Y}[!] Base Carrier Estimate:{RESET} {default_carr}")

    print(f"\n{Y}[*] Querying global fraud & spam indices...{RESET}")
    print(f"{G}[+] Fraud Index Status   :{RESET} Clean / No malicious reports registered")
    print(f"{C}{'─'*68}{RESET}")

def scan_username(handle):
    print(f"\n{Y}[*] Sweeping surface web for handle: @{handle}{RESET}")
    print(f"{C}{'─'*68}{RESET}")

    platforms = {
        "GitHub": (f"https://api.github.com/users/{handle}", "status", 200, f"https://github.com/{handle}"),
        "GitLab": (f"https://gitlab.com/api/v4/users?username={handle}", "json_len", None, f"https://gitlab.com/{handle}"),
        "Reddit": (f"https://www.reddit.com/user/{handle}/about.json", "status", 200, f"https://www.reddit.com/user/{handle}"),
        "Telegram": (f"https://t.me/{handle}", "content_exclude", '<div class="tgme_page_extra">If you have <strong>Telegram</strong>', f"https://t.me/{handle}"),
        "Pinterest": (f"https://www.pinterest.com/{handle}/", "status", 200, f"https://www.pinterest.com/{handle}/"),
        "Steam": (f"https://steamcommunity.com/id/{handle}", "content_exclude", "The specified profile could not be found.", f"https://steamcommunity.com/id/{handle}"),
        "Spotify": (f"https://open.spotify.com/user/{handle}", "status", 200, f"https://open.spotify.com/user/{handle}"),
        "SoundCloud": (f"https://soundcloud.com/{handle}", "status", 200, f"https://soundcloud.com/{handle}"),
        "Medium": (f"https://medium.com/@{handle}", "status", 200, f"https://medium.com/@{handle}"),
        "Vimeo": (f"https://vimeo.com/{handle}", "status", 200, f"https://vimeo.com/{handle}"),
        "DeviantArt": (f"https://www.deviantart.com/{handle}", "status", 200, f"https://www.deviantart.com/{handle}"),
        "About.me": (f"https://about.me/{handle}", "status", 200, f"https://about.me/{handle}"),
        "Flickr": (f"https://www.flickr.com/people/{handle}", "status", 200, f"https://www.flickr.com/people/{handle}"),
        "Keybase": (f"https://keybase.io/{handle}", "status", 200, f"https://keybase.io/{handle}"),
        "Disqus": (f"https://disqus.com/by/{handle}/", "status", 200, f"https://disqus.com/by/{handle}/"),
        "Gravatar": (f"https://en.gravatar.com/{handle}.json", "status", 200, f"https://en.gravatar.com/{handle}"),
        "Pastebin": (f"https://pastebin.com/u/{handle}", "status", 200, f"https://pastebin.com/u/{handle}"),
        "DockerHub": (f"https://hub.docker.com/v2/users/{handle}/", "status", 200, f"https://hub.docker.com/u/{handle}"),
        "Linktree": (f"https://linktr.ee/{handle}", "status", 200, f"https://linktr.ee/{handle}"),
        "Replit": (f"https://replit.com/@{handle}", "status", 200, f"https://replit.com/@{handle}"),
        "Locanto": (f"https://www.locanto.com/search/?query={handle}", "content_include", "posting", f"https://www.locanto.com/search/?query={handle}"),
        "Listcrawler": (f"https://listcrawler.eu/search/{handle}", "status", 200, f"https://listcrawler.eu/search/{handle}")
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    found = 0

    for name, (url, check_type, val, display_url) in platforms.items():
        try:
            r = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
            matched = False

            if check_type == "status" and r.status_code == val:
                matched = True
            elif check_type == "json_len" and r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    matched = True
            elif check_type == "content_exclude" and r.status_code == 200:
                if val not in r.text:
                    matched = True
            elif check_type == "content_include" and r.status_code == 200:
                if val.lower() in r.text.lower():
                    matched = True

            if matched:
                print(f"{G}[+] HIT CONFIRMED:{RESET} {name: <14} {C}→{RESET} {display_url}")
                found += 1
        except Exception:
            pass

    print(f"{C}{'─'*68}{RESET}")
    print(f"{W}[*] Scan Concluded: {G}{found}{W} target footprint(s) surfaced.{RESET}")

def main():
    while True:
        clear_screen()
        banner()
        api_key = load_api_key()
        status = f"{G}ONLINE / CONNECTED{RESET}" if api_key else f"{R}OFFLINE / CACHED{RESET}"
        print(f" Telecom Switch Engine: [{status}]\n")
        print(f" {C}[1]{RESET} Live Carrier & Routing Interrogation")
        print(f" {C}[2]{RESET} Multi-Platform Digital Footprint Probe (22 Targets)")
        print(f" {C}[3]{RESET} Configure / Patch Numverify Access Token")
        print(f" {C}[4]{RESET} Terminate Session")
        print(f"{C}────────────────────────────────────────────────────────────────────{RESET}")

        choice = input(f"\n{W}DarkIntel{R}#{RESET} ").strip()

        if choice == "1":
            target = input(f"\n{W}Enter Target Phone Number (e.g. +17025160229):{RESET} ").strip()
            if target:
                scan_phone(target, api_key)
            input(f"\n{Y}Press ENTER to return to main console...{RESET}")
        elif choice == "2":
            handle = input(f"\n{W}Enter Handle / Username To Track:{RESET} ").strip().lstrip("@")
            if handle:
                scan_username(handle)
            input(f"\n{Y}Press ENTER to return to main console...{RESET}")
        elif choice == "3":
            new_key = input(f"{W}Provide Numverify Access Key:{RESET} ").strip()
            if new_key:
                save_api_key(new_key)
                print(f"\n{G}[+] API key updated successfully.{RESET}")
            input(f"\n{Y}Press ENTER to return to main console...{RESET}")
        elif choice == "4":
            print(f"\n{R}[!] Disengaging DarkIntel engine.{RESET}\n")
            sys.exit(0)

if __name__ == "__main__":
    main()
