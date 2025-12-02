import requests
from bs4 import BeautifulSoup
import time
import threading
from telegram import Bot

TOKEN = "8339238687:AAHPxsVPZwxIO1uKsxpf93VzU0fFEGBkI7I"
CHAT_ID = "-1003344294459"

bot = Bot(token=TOKEN)

# -------------------------------------------
# SITE LIST
# -------------------------------------------
SITES = {
    "satta-king-fast.com": "https://satta-king-fast.com/",
    "mysattakings.com": "https://mysattakings.com/",
    "sattakingno.in": "https://sattakingno.in/",
    "sattakingno.org": "https://sattakingno.org/"
}

# -------------------------------------------
# MARKETS TO TRACK
# -------------------------------------------
TARGET_MARKETS = {
    "DESAWAR": ["DESAWAR", "DISAWER", "DS", "DSAWAR"],
    "FARIDABAD": ["FARIDABAD", "FB"],
    "GHAZIABAD": ["GHAZIABAD", "GAZIYABAD", "GB"],
    "GALI": ["GALI", "GL"]
}

# --------------------------------------------
# Store last seen results
# --------------------------------------------
last_data = {
    "DESAWAR": {},
    "FARIDABAD": {},
    "GHAZIABAD": {},
    "GALI": {}
}


# =======================================================
# SCRAPER 1 — satta-king-fast.com
# =======================================================
def parse_fast(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    for tr in soup.select("tr.game-result"):
        game = tr.get("id", "").strip().upper()
        name_tag = tr.select_one(".game-name")
        
        if not name_tag:
            continue

        name = name_tag.text.strip().upper()
        today = tr.select_one("td.today-number h3")

        if today:
            results[name] = today.text.strip()

    return results


# =======================================================
# SCRAPER 2 — mysattakings.com
# =======================================================
def parse_mysattakings(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    for tr in soup.select("tr.game-result"):
        name_tag = tr.select_one(".game-name")
        if not name_tag:
            continue

        name = name_tag.text.strip().upper()
        tds = tr.select(".today-number p")
        if len(tds) >= 2:
            result = tds[1].text.strip()
            results[name] = result

    return results


# =======================================================
# SCRAPER 3 & 4 — sattakingno.in / sattakingno.org
# =======================================================
def parse_no_sites(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    for tr in soup.select("table.resultboard tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        name = tds[0].text.split("<")[0].strip().upper()
        today = tds[2].text.strip().replace(" ", "")

        if today:
            results[name] = today

    return results


# =======================================================
# Fetch + Parse Dispatcher
# =======================================================
def fetch_site(site, url):
    try:
        r = requests.get(url, timeout=10)
        html = r.text

        if "satta-king-fast.com" in url:
            return parse_fast(html)
        if "mysattakings.com" in url:
            return parse_mysattakings(html)
        if "sattakingno.in" in url or "sattakingno.org" in url:
            return parse_no_sites(html)

    except Exception as e:
        return {}


# =======================================================
# Normalize Market Name
# =======================================================
def match_market(name):
    clean = name.upper().strip()

    # Exact names ONLY
    EXACT_NAMES = {
        "DESAWAR": ["DESAWAR", "DISAWER"],
        "FARIDABAD": ["FARIDABAD"],
        "GHAZIABAD": ["GHAZIABAD", "GAZIABAAD", "GAZIYABAD"],
        "GALI": ["GALI"]
    }

    for market, names in EXACT_NAMES.items():
        for n in names:
            if clean == n:
                return market

    return None



# =======================================================
# MAIN MONITORING LOOP
# =======================================================
def monitor():
    global last_data

    while True:
        combined = {
            "DESAWAR": {},
            "FARIDABAD": {},
            "GHAZIABAD": {},
            "GALI": {}
        }

        # Fetch from all 4 sites
        for sitename, link in SITES.items():
            data = fetch_site(sitename, link)

            for name, value in data.items():
                m = match_market(name)
                if m:
                    combined[m][sitename] = value

        # Compare with last data
        for market in combined:
            if combined[market] != last_data[market]:
                # POST UPDATE TO TELEGRAM
                send_update(market, combined[market], last_data[market])
                last_data[market] = combined[market]

        time.sleep(10)  # 10-second interval


# =======================================================
# TELEGRAM SENDER
# =======================================================
def send_update(market, new_data, old_data):
    text = f"📡 *{market} Result Update*\n\n"

    for site, result in new_data.items():
        text += f"🔹 `{site}` → *{result}*\n"

    # Detect first publisher
    completed = {s: r for s, r in new_data.items() if r != "" and r != "XX"}
    if completed:
        first_site = list(completed.keys())[0]
        text += f"\n🔥 *First to upload:* `{first_site}`"

    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")


# =======================================================
# START BOT
# =======================================================
threading.Thread(target=monitor).start()
print("Bot started and monitoring...")


