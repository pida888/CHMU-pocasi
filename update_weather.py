import json
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

STATIONS = {
    "bor": "0-203-0-10202083001",   # Borohrádek
    "pce": "0-20000-0-11652",       # Pardubice, letiště
}


def get_latest_temp(station_id: str) -> float | None:
    # Soubory ČHMÚ se řídí UTC datem a nový denní soubor vzniká kolem 01:15 UTC
    file_date = (datetime.now(timezone.utc) - timedelta(hours=1, minutes=15)).strftime("%Y%m%d")
    url = f"https://opendata.chmi.cz/meteorology/climate/now/data/10m-{station_id}-{file_date}.json"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        values = payload["data"]["data"]["values"]
        temps = [float(row[3]) for row in values if len(row) > 3 and row[1] == "T" and row[3] is not None]
        return round(temps[-1], 1) if temps else None
    except Exception as e:
        print(f"Chyba při stahování {station_id}: {e}")
        return None


def main() -> None:
    bor = get_latest_temp(STATIONS["bor"])
    pce = get_latest_temp(STATIONS["pce"])

    # Výpočet váženého průměru pro Holice se zálohou při výpadku jedné stanice
    if bor is not None and pce is not None:
        hol = round((2 * bor + pce) / 3, 1)
    elif bor is not None:
        hol = bor
    elif pce is not None:
        hol = pce
    else:
        hol = None

    prague_now = datetime.now(ZoneInfo("Europe/Prague")).strftime("%H:%M")

    output = {
        "bor": bor,
        "pce": pce,
        "hol": hol,
        "updated": prague_now,
    }

    with open("pocasi.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    print("Uloženo:", output)


if __name__ == "__main__":
    main()
