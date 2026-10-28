"""Netherlands drug shortage scraper.

Source: Farmanco (farmanco.knmp.nl), the public medicine shortage list run by
KNMP, the Royal Dutch Pharmacists Association. Uses requests + BeautifulSoup.
"""
import copy
import csv
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import output_path, REQUEST_DELAY


def parse_end_date(date_str):
    """Parse various end date formats including quarters, Dutch phrases, and normal dates"""
    if not date_str or not isinstance(date_str, str):
        return date_str

    date_str = date_str.strip().lower()

    # Handle special Dutch phrases
    if any(phrase in date_str for phrase in ["uit de handel", "product niet actief", "onbekend"]):
        return date_str  # "Discontinued"

        # First check for the special "áµ‰" character case
    if "áµ‰" in date_str:
        try:
            # Extract quarter and year from formats like "3áµ‰ kwartaal 2025"
            parts = date_str.split()
            quarter = int(parts[0].replace("áµ‰", ""))
            year = parts[2]

            quarter_dates = {
                1: "15/02/",  # Q1: February 15
                2: "15/05/",  # Q2: May 15
                3: "15/08/",  # Q3: August 15
                4: "15/11/"  # Q4: November 15
            }

            if quarter in quarter_dates:
                return f"{quarter_dates[quarter]}{year}"
        except:
            pass

    # Handle other quarter formats (3e kwartaal 2025, 3ème kwartaal 2025)
    quarter_match = re.match(r'(\d+)(?:e|è|me?)?\s*kwartaal\s*(\d{4})', date_str)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        year = int(quarter_match.group(2))

        quarter_dates = {
            1: "15/02/",  # Q1: February 15
            2: "15/05/",  # Q2: May 15
            3: "15/08/",  # Q3: August 15
            4: "15/11/"  # Q4: November 15
        }

        if quarter in quarter_dates:
            return f"{quarter_dates[quarter]}{year}"
        return f"Q{quarter} {year}"

    # Handle week numbers (week 40 2025)
    week_match = re.match(r'week\s*(\d+)\s*(\d{4})', date_str)
    if week_match:
        week_num = int(week_match.group(1))
        year = int(week_match.group(2))
        try:
            # Get the Monday of the given week and add 3 days to get Thursday (mid-week)
            date = datetime.strptime(f"{year}-W{week_num - 1}-1", "%Y-W%W-%w") + timedelta(days=3)
            return date.strftime("%d/%m/%Y")
        except:
            return f"Week {week_num} {year}"

    # Handle Dutch months (maart 2026)
    month_map = {
        'januari': '01', 'februari': '02', 'maart': '03', 'april': '04',
        'mei': '05', 'juni': '06', 'juli': '07', 'augustus': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
    }

    for month_name, month_num in month_map.items():
        if month_name in date_str:
            year_match = re.search(r'\d{4}', date_str)
            year = year_match.group(0) if year_match else datetime.now().year
            return f"15/{month_num}/{year}"  # Mid-month date

    # Handle standard date formats (DD/MM/YYYY)
    date_match = re.match(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if date_match:
        day, month, year = date_match.groups()
        try:
            datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
            return f"{day}/{month}/{year}"
        except ValueError:
            pass

    # Handle year only (2025)
    if re.match(r'^\d{4}$', date_str):
        return f"01/07/{date_str}"  # Mid-year: July 1st

    split_list = date_str.split()
    if len(split_list) == 2:
        if split_list[0] in month_map:
            _month = month_map[split_list[0]]
            return f"15/{_month}/{split_list[0]}"

    if "áµ‰ kwartaal" in date_str or "áµ kwartaal" in date_str or ("aµ" in date_str and "kwartaal" in date_str):
        try:
            _quarter_year = date_str.split()
            quarter_dates = {
                1: "15/02/",  # Q1: February 15
                2: "15/05/",  # Q2: May 15
                3: "15/08/",  # Q3: August 15
                4: "15/11/"  # Q4: November 15
            }
            return f"{quarter_dates[int(date_str[0])]}{_quarter_year[2]}"
        except ValueError:
            pass

    if "kwartaal" in date_str:
        try:
            _quarter_year = date_str.split()
            quarter_dates = {
                1: "15/02/",  # Q1: February 15
                2: "15/05/",  # Q2: May 15
                3: "15/08/",  # Q3: August 15
                4: "15/11/"  # Q4: November 15
            }
            return f"{quarter_dates[int(date_str[0])]}{_quarter_year[2]}"
        except ValueError:
            pass

    return date_str  # Default for unparseable dates


def parse_main_date(date_str):
    """Parse dates from the main page with Dutch month abbreviations"""
    if not date_str:
        return ""

    month_map = {
        'jan': 1, 'feb': 2, 'mrt': 3, 'apr': 4, 'mei': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
    }

    parts = date_str.split()
    if len(parts) == 3:
        day = parts[0].zfill(2)
        month_str = parts[1].replace('.', '').lower()[:3]
        year = parts[2]
        if month_str in month_map:
            return f"{day}/{month_map[month_str]:02d}/{year}"

    return date_str


def write_output_file(data, filename, fieldnames):
    """Write a list of dicts to a CSV file (overwrites an existing file)."""
    try:
        with open(filename, mode="w", newline="", encoding="utf-8", errors="replace") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        print(f"Failed to write {filename}: {e}")


def main():
    base_url = "https://farmanco.knmp.nl/"
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    output_file = output_path("netherlands", "shortages", "csv")

    print("Fetching main page...")
    response = session.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a", class_="shortage-flex-table")
    print(f"Found {len(links)} products")

    fieldnames = [
        "Country", "ATC3 code", "ATC4 code", "Molecule", "Product Name",
        "Product Strength", "Product Pack Size", "Corporation", "Shortage Status",
        "Date reported", "Start date", "End date", "Date last updated",
        "Relevant unit number", "Alternatives available", "Shortage impact rating",
        "Additional commentary"
    ]

    records = []

    for a_tag in links:
        base_dict = {
            "Country": "Netherlands",
            "Relevant unit number": "",
            "Alternatives available": "",
            "ATC3 code": "",
            "ATC4 code": "",
        }

        # Extract main page data
        base_dict["Molecule"] = a_tag.find("li", class_="sort-active-ingredient").get_text(strip=True) if a_tag.find(
            "li", class_="sort-active-ingredient") else ""
        impact = a_tag.find("li", class_="sort-preferential").get_text(strip=True) if a_tag.find("li",
                                                                                                 class_="sort-preferential") else ""
        base_dict["Shortage impact rating"] = "High" if impact == "Ja" else ""

        date_str = a_tag.find("li", class_="sort-date active").get_text(strip=True) if a_tag.find("li",
                                                                                                  class_="sort-date active") else ""
        base_dict["Start date"] = parse_main_date(date_str)
        base_dict["Date last updated"] = base_dict["Start date"]

        # Process detail page
        detail_url = urljoin(base_url, a_tag.get("href"))
        # print(f"Processing: {detail_url}")
        try:
            time.sleep(REQUEST_DELAY)  # Polite delay between requests
            detail_response = session.get(detail_url)
            detail_response.raise_for_status()
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")

            for entry in detail_soup.find_all("div", class_="expandable mainlevel shortage public"):
                product_dict = copy.deepcopy(base_dict)
                items = entry.select(".expandable-header .item")

                if items:
                    product_dict.update({
                        "Product Name": items[0].get_text(strip=True) if len(items) > 0 else "",
                        "Corporation": items[1].get_text(strip=True) if len(items) > 1 else "",
                        "Product Pack Size": items[2].get_text(strip=True) if len(items) > 2 else "",
                        "Shortage Status": items[3].get_text(strip=True) if len(items) > 3 else ""
                    })

                # Handle end date
                expected_date = entry.select_one(".expandable-header .date .value")
                end_date_str = expected_date.get_text(strip=True) if expected_date else ""
                product_dict["End date"] = parse_end_date(end_date_str)

                # Additional fields
                h3 = entry.find_previous("h3", class_="tocEntry")
                product_dict["Product Strength"] = h3.get_text(strip=True) if h3 else ""

                shortage_reason = entry.select_one("div.wrapper.flex p")
                product_dict["Additional commentary"] = shortage_reason.get_text(strip=True) if shortage_reason else ""

                # Set Date Reported
                today_date = datetime.now().date()

                # Use Date last updated if available and in the past
                if product_dict["Date last updated"]:
                    try:
                        # Parse the date in DD/MM/YYYY format
                        last_updated = datetime.strptime(product_dict["Date last updated"], "%d/%m/%Y").date()

                        # Only use it if it's today or in the past
                        if last_updated <= today_date:
                            product_dict["Date reported"] = product_dict["Date last updated"]
                        else:
                            # If it's in the future, use today's date
                            product_dict["Date reported"] = today_date.strftime("%d/%m/%Y")
                    except ValueError:
                        # If parsing fails, use today's date
                        product_dict["Date reported"] = today_date.strftime("%d/%m/%Y")
                else:
                    # If no last updated date, use today's date
                    product_dict["Date reported"] = today_date.strftime("%d/%m/%Y")

                records.append(product_dict)

        except Exception as e:
            print(f"Error processing {detail_url}: {str(e)}")

    write_output_file(records, output_file, fieldnames)
    print(f"Saved {len(records)} records to {output_file}")


if __name__ == "__main__":
    main()
