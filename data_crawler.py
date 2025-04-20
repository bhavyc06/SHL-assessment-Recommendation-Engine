import os, time, json, requests
from bs4 import BeautifulSoup

def crawl_assessments():
    os.makedirs("data", exist_ok=True)
    assessments = []

    # 1) Loop pages 1–32
    for page in range(1, 33):
        url = f"https://www.shl.com/solutions/products/product-catalog/?page={page}&type=1"
        resp = requests.get(url); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # find the table whose first <th> is "Individual Test Solutions"
        tables = soup.find_all("table")
        table = None
        for tbl in tables:
            th = tbl.find("th")
            if th and th.get_text(strip=True).startswith("Individual Test Solutions"):
                table = tbl
                break
        # fallback: if no such table, assume the second one
        if table is None and len(tables) >= 2:
            table = tables[1]
        if table is None:
            print(f"Page {page}: no suitable table, skipping")
            continue

        rows = table.find_all("tr")[1:]  # skip header
        if not rows:
            print(f"Page {page}: no rows, stopping pagination")
            break

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            a = cells[0].find("a", href=True)
            if not a:
                continue
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.shl.com" + link

            assessments.append({
                "name":       a.get_text(strip=True),
                "url":        link,
                "remote":     cells[1].get_text(strip=True) or "No",
                "adaptive":   cells[2].get_text(strip=True) or "No",
                "test_type":  cells[3].get_text(strip=True)
            })

        print(f"Page {page}: parsed {len(rows)} items")
        time.sleep(1)

    # 2) Fetch detail pages for description & duration
    print(f"\nFetching detail for {len(assessments)} assessments…")
    for a in assessments:
        try:
            r2 = requests.get(a["url"]); r2.raise_for_status()
            detail = BeautifulSoup(r2.text, "html.parser")

            # primary description selector
            desc = detail.select_one(".product-description")
            text = desc.get_text(" ", strip=True) if desc else ""

            # fallback #1: meta[name="description"]
            if not text:
                m = detail.find("meta", {"name": "description"})
                text = m["content"].strip() if m and m.get("content") else ""

            # fallback #2: meta[property="og:description"]
            if not text:
                og = detail.find("meta", {"property": "og:description"})
                text = og["content"].strip() if og and og.get("content") else ""

            a["description"] = text

            # Completion Time → digits
            dur = detail.find(text=lambda t: "Completion Time" in t)
            if dur:
                nums = "".join(ch for ch in dur if ch.isdigit())
                a["duration_minutes"] = int(nums) if nums else None
            else:
                a["duration_minutes"] = None

            time.sleep(0.2)
        except Exception as e:
            print("⚠️", a["url"], "→", e)
            a["description"] = ""
            a["duration_minutes"] = None

    # 3) Save JSON
    with open("data/assessments.json", "w", encoding="utf-8") as f:
        json.dump(assessments, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Wrote {len(assessments)} assessments to data/assessments.json")

if __name__ == "__main__":
    crawl_assessments()
