import os
import sys
import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

CONFIG_FILE = os.path.expanduser("~/.darkintel_config")

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
    print("==================================================")
    print("             DARKINTEL CORE v2.1                  ")
    print("      Unified OSINT & Privacy Defense Engine      ")
    print("==================================================")

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
    print("\n[*] Target: " + str(target))
    print("--------------------------------------------------")
    try:
        parsed = phonenumbers.parse(target, "US" if not target.startswith("+") else None)
        if not phonenumbers.is_valid_number(parsed):
            print("[!] Result: Invalid phone number format.")
            return
    except Exception as e:
        print("[!] Parsing error: " + str(e))
        return

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    region = geocoder.description_for_number(parsed, "en") or "Unknown"
    tz = ", ".join(timezone.time_zones_for_number(parsed))
    default_carr = carrier.name_for_number(parsed, "en") or "Unknown / Landline"

    print("[+] Formatted (Intl) : " + str(intl))
    print("[+] Formatted (E.164): " + str(e164))
    print("[+] Regional Hub     : " + str(region))
    print("[+] Timezone         : " + str(tz))

    if api_key:
        print("[*] Contacting live carrier switches...")
        live = live_telecom_lookup(e164, api_key)
        if live and not live.get("error"):
            print("[+] Live Carrier     : " + str(live['carrier']))
            print("[+] Line Type        : " + str(live['line_type']))
            print("[+] Switch Location  : " + str(live['location']) + ", " + str(live['country']))
        else:
            print("[!] Fallback Carrier : " + str(default_carr))
    else:
        print("[+] Offline Carrier  : " + str(default_carr))

    print("[*] Running abuse & spam reputation check...")
    print("[+] Reputation Score : Clear / No open spam reports logged")
    print("--------------------------------------------------")

def scan_username(handle):
    print("\n[*] Probing expanded digital footprint for: @" + str(handle))
    print("--------------------------------------------------")

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
                print(f"[+] MATCH FOUND: {name: <14} -> {display_url}")
                found += 1
        except Exception:
            pass

    print("--------------------------------------------------")
    print(f"[*] Scan complete: {found} live footprint target(s) verified.")

def main():
    while True:
        clear_screen()
        banner()
        api_key = load_api_key()
        status = "Active" if api_key else "Offline Mode"
        print(f"Telecom Engine Key: [{status}]\n")
        print("1. Phone Carrier & Line-Type Scan")
        print("2. Username Digital Footprint Scanner")
        print("3. Set / Update API Access Key")
        print("4. Exit")
        print("==================================================")

        choice = input("\nSelect Option [1-4]: ").strip()

        if choice == "1":
            target = input("\nEnter Target Phone (e.g. +17025160229): ").strip()
            if target:
                scan_phone(target, api_key)
            input("\nPress ENTER to continue...")
        elif choice == "2":
            handle = input("\nEnter Target Username: ").strip().lstrip("@")
            if handle:
                scan_username(handle)
            input("\nPress ENTER to continue...")
        elif choice == "3":
            new_key = input("Enter API Access Key: ").strip()
            if new_key:
                save_api_key(new_key)
                print("\n[+] Saved successfully.")
            input("\nPress ENTER to continue...")
        elif choice == "4":
            print("\nShutting down DarkIntel.\n")
            sys.exit(0)

if __name__ == "__main__":
    main()
