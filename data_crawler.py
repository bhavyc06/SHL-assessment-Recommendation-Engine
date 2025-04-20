import os
import time
import json
import requests
from bs4 import BeautifulSoup

def crawl_assessments():
    # ensure the data folder exists
    os.makedirs("data", exist_ok=True)

    assessments = []

    # Loop pages 1–32
    for page in range(1, 33):
        url = f"https://www.shl.com/solutions/products/product-catalog/?page={page}&type=1"
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the “Individual Test Solutions” table
        table = None
        for tbl in soup.find_all("table"):
            prev_text = tbl.find_previous_sibling(text=True)
            if prev_text and "Individual Test Solutions" in prev_text.strip():
                table = tbl
                break
        if table is None and soup.find_all("table"):
            table = soup.find_all("table")[-1]

        if not table:
            print(f"Page {page}: ❌ no table found, skipping")
            continue

        rows = table.find_all("tr")
        if len(rows) <= 1:
            print(f"Page {page}: no entries found, stopping pagination.")
            break

        # Parse each data row (skip header at index 0)
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            a_tag = cells[0].find("a", href=True)
            if not a_tag:
                continue

            name = a_tag.get_text(strip=True)
            link = a_tag["href"]
            if not link.startswith("http"):
                link = "https://www.shl.com" + link

            remote   = cells[1].get_text(strip=True) or "No"
            adaptive = cells[2].get_text(strip=True) or "No"
            test_type= cells[3].get_text(strip=True)

            assessments.append({
                "name": name,
                "url": link,
                "remote": remote,
                "adaptive": adaptive,
                "test_type": test_type
            })

        print(f"Page {page}: parsed {len(rows)-1} assessments")
        time.sleep(1)  # be polite

    # Now fetch detail pages for description & duration
    print(f"\nFetching detail pages for {len(assessments)} assessments…")
    for item in assessments:
        try:
            r2 = requests.get(item["url"])
            r2.raise_for_status()
            detail = BeautifulSoup(r2.text, "html.parser")

            desc_tag = detail.select_one(".product-description")
            item["description"] = desc_tag.get_text(strip=True) if desc_tag else ""

            dur_text = detail.find(text=lambda t: "Completion Time" in t)
            if dur_text:
                digits = "".join(filter(str.isdigit, dur_text))
                item["duration_minutes"] = int(digits) if digits else None
            else:
                item["duration_minutes"] = None

            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️  Failed to fetch {item['url']}: {e}")
            item["description"] = ""
            item["duration_minutes"] = None

    # Save to JSON
    out_path = "data/assessments.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(assessments, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(assessments)} assessments to {out_path}")

if __name__ == "__main__":
    crawl_assessments()
