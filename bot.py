import requests
from bs4 import BeautifulSoup
import time
import threading
from telegram import Bot

# ------------------------------------
# TELEGRAM CONFIG
# ------------------------------------
TOKEN = "8339238687:AAHPxsVPZwxIO1uKsxpf93VzU0fFEGBkI7I"
CHAT_ID = "-1003344294459"

bot = Bot(token=TOKEN)

# ------------------------------------
# SITES TO SCRAPE
# ------------------------------------
SITES = {
    "satta-king-fast.com": "https://satta-king-fast.com/",
    "mysattakings.com": "https://mysattakings.com/",
    "sattakingno.in": "https://sattakingno.in/",
    "sattakingno.org": "https://sattakingno.org/",
    "satta-king-fix-no.in": "https://satta-king-fix-no.in/",
    "sattakingdarbar.org": "https://sattakingdarbar.org/",
    "satta-sport.in": "https://satta-sport.in/",
    "raj-darbar.com": "https://raj-darbar.com/",
    "satta-badshah.com": "https://satta-badshah.com/",
    "kingsofsatta.com": "https://kingsofsatta.com/"
}

# ------------------------------------
# MARKETS
# ------------------------------------
TARGET_MARKETS = ["DESAWAR", "FARIDABAD", "GHAZIABAD", "GALI"]

# Store last seen values
last_data = {m: {} for m in TARGET_MARKETS}

# ------------------------------------
# VALID RESULT FILTER
# ------------------------------------
def is_valid_result(value):
    return value.isdigit() and len(value) <= 3


# ======================================================
# SCRAPER 1 — satta-king-fast.com
# ======================================================
def parse_fast(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for tr in soup.select("tr.game-result"):
        name_tag = tr.select_one(".game-name")
        if not name_tag:
            continue
        name = name_tag.text.strip().upper()
        today_tag = tr.select_one("td.today-number h3")
        if today_tag:
            today = today_tag.text.strip()
            if is_valid_result(today):
                results[name] = today
    return results


# ======================================================
# SCRAPER 2 — mysattakings.com
# ======================================================
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
            today = tds[1].text.strip()
            if is_valid_result(today):
                results[name] = today
    return results


# ======================================================
# SCRAPER 3 & 4 — sattakingno.in / sattakingno.org
# ======================================================
def parse_no_sites(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    table = soup.find("table", class_="resultboard")
    if not table:
        return results
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        name_raw = cols[0].get_text(" ", strip=True).upper()
        name_clean = name_raw.split("(")[0].strip().split()[0]
        today = cols[2].get_text(strip=True).replace(" ", "").upper()
        if "DISAWER" in name_clean or "DESAWAR" in name_clean:
            market = "DESAWAR"
        elif "FARIDABAD" in name_clean:
            market = "FARIDABAD"
        elif "GAZIYABAD" in name_clean or "GHAZIABAD" in name_clean:
            market = "GHAZIABAD"
        elif "GALI" in name_clean:
            market = "GALI"
        else:
            continue
        if is_valid_result(today):
            results[market] = today
    return results


# ======================================================
# SCRAPER 5 — satta-king-fix-no.in
# ======================================================
def parse_fixno(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for div in soup.select("div.gboardhalf"):
        name_tag = div.select_one(".gbgamehalf")
        new_tag = div.select_one(".gbhalfresultn")
        if not name_tag or not new_tag:
            continue
        name = name_tag.text.strip().upper()
        new = new_tag.text.replace("[", "").replace("]", "").strip()
        if is_valid_result(new):
            results[name] = new
    return results


# ======================================================
# SCRAPER 6 — sattakingdarbar.org
# ======================================================
def parse_darbar(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for div in soup.select("div.border"):
        name_tag = div.find("font", style=lambda v: v and "font-size:18px" in v)
        new_tag = div.find("font", style=lambda v: v and "font-size:25px" in v and "color:blue" in v)
        if not name_tag or not new_tag:
            continue
        name = name_tag.text.strip().upper()
        new = new_tag.text.replace("[", "").replace("]", "").strip()
        if is_valid_result(new):
            results[name] = new
    return results


# ======================================================
# SCRAPER 7 — satta-sport.in
# ======================================================
def parse_sport(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for div in soup.select("div[align='center']"):
        name_tag = div.find("a")
        new_tag = div.find("span", style=lambda v: v and "font-size:20px" in v)
        if not name_tag or not new_tag:
            continue
        name = name_tag.text.strip().upper()
        new = new_tag.text.replace("[", "").replace("]", "").strip()
        if is_valid_result(new):
            results[name] = new
    return results


# ======================================================
# SCRAPER 8 — raj-darbar.com
# ======================================================
def parse_rajdarbar(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for div in soup.select("div.border"):
        text = div.get_text(" ", strip=True).upper()
        for market in ["DESAWAR", "FARIDABAD", "GHAZIABAD", "GALI"]:
            if market in text:
                new = text.split("[")[-1].split("]")[0].strip()
                if is_valid_result(new):
                    results[market] = new
    return results


# ======================================================
# SCRAPER 9 — satta-badshah.com
# ======================================================
def parse_badshah(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for div in soup.select("div.border"):
        text = div.get_text(" ", strip=True).upper()
        for market in ["DESAWAR", "FARIDABAD", "GHAZIABAD", "GALI"]:
            if market in text:
                new = text.split("[")[-1].split("]")[0].strip()
                if is_valid_result(new):
                    results[market] = new
    return results


# ======================================================
# SCRAPER 10 — kingsofsatta.com
# ======================================================
def parse_kingsofsatta(html):
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for tr in soup.select("tr.game-result"):
        name_tag = tr.select_one(".game-name")
        today_tag = tr.select_one("td.today-number h3")
        if not name_tag or not today_tag:
            continue
        name = name_tag.text.strip().upper()
        today = today_tag.text.strip()
        if is_valid_result(today):
            results[name] = today
    return results


# ======================================================
# Fetch Dispatcher
# ======================================================
def fetch_site(sitename, url):
    try:
        r = requests.get(url, timeout=10)
        html = r.text
        if "satta-king-fast.com" in sitename:
            return parse_fast(html)
        if "mysattakings.com" in sitename:
            return parse_mysattakings(html)
        if "sattakingno.in" in sitename or "sattakingno.org" in sitename:
            return parse_no_sites(html)
        if "satta-king-fix-no.in" in sitename:
            return parse_fixno(html)
        if "sattakingdarbar.org" in sitename:
            return parse_darbar(html)
        if "satta-sport.in" in sitename:
            return parse_sport(html)
        if "raj-darbar.com" in sitename:
            return parse_rajdarbar(html)
        if "satta-badshah.com" in sitename:
            return parse_badshah(html)
        if "kingsofsatta.com" in sitename:
            return parse_kingsofsatta(html)
    except Exception:
        return {}


# ======================================================
# Telegram Message Sender
# ======================================================
def send_update(market, new_data):
    text = f"📡 *{market} Result Update*\n\n"
    for site, result in new_data.items():
        text += f"🔹 `{site}` → *{result}*\n"
    if len(new_data) > 0:
        first = list(new_data.keys())[0]
        text += f"\n🔥 *First to upload:* `{first}`"
    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")


# ======================================================
# Monitor Loop
# ======================================================
def monitor():
    global last_data

    while True:
        combined = {m: {} for m in TARGET_MARKETS}

        # Fetch from all sites
        for sitename, url in SITES.items():
            data = fetch_site(sitename, url)

            for name, value in data.items():
                if name in TARGET_MARKETS and is_valid_result(value):
                    combined[name][sitename] = value

        # Check each market independently
        for market in TARGET_MARKETS:

            new_values = combined[market]
            old_values = last_data[market]

            # If NO numeric result exists → ignore
            if len(new_values) == 0:
                continue

            # Extract only the numeric values from both
            new_numbers = sorted(new_values.values())
            old_numbers = sorted(old_values.values())

            # If numbers SAME → do not send update
            if new_numbers == old_numbers:
                continue

            # Otherwise → SEND UPDATE
            send_update(market, new_values)

            # Save latest values
            last_data[market] = new_values

        time.sleep(10)


# ======================================================
# START BOT
# ======================================================
threading.Thread(target=monitor).start()
print("Bot started and monitoring...")

