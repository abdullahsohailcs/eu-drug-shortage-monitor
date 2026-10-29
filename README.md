# EU Drug Shortage Monitor

Python | pandas | Playwright | Requests | BeautifulSoup

Collects official medicine-shortage data from five European regulators and normalises it into one shared format, so the countries can be compared side by side. Each source needs a different technique: a public API, JSON behind a search page, static HTML, a list that only loads as you scroll, and a paginated form.

---

## Sources

| Country | Source | Technique |
| --- | --- | --- |
| Belgium | [pharmastatus.be](https://pharmastatus.be/human/medical-products) (FAMHP) | Playwright + the site's public pack-info API |
| Finland | [Fimea shortage search](https://fimea.fi/en/databases_and_registers/shortages) | Requests against the JSON behind the search page |
| Netherlands | [Farmanco](https://farmanco.knmp.nl/) (KNMP) | Requests + BeautifulSoup |
| Spain | [CIMA supply problems](https://cima.aemps.es/cima/publico/listadesabastecimiento.html) (AEMPS) | Playwright with auto-scroll for a dynamic list |
| Portugal | [INFOMED](https://extranet.infarmed.pt/INFOMED-fo/pesquisa-avancada.xhtml) (INFARMED) | Playwright with form filters and pagination |

**Fields collected** (where the source provides them): country, ATC3 and ATC4 codes, molecule, product name, strength, pack size, manufacturer, shortage status, date reported, start date, expected end date, date last updated, alternatives available, shortage impact rating and the source's own commentary.

**Problems solved along the way:**

- Dutch end dates written as quarters ("3e kwartaal 2025"), week numbers ("week 26 2025") or month names, normalised to `DD/MM/YYYY`
- Pack counts pulled from free-text product names, and ATC3 codes derived from ATC4
- A dynamic Spanish list that only loads as you scroll
- Records with missing key fields saved to a separate errors file instead of silently dropped

---

## Sample output

Real output from earlier runs, trimmed to 20 rows each:

- [samples/finland_sample.csv](samples/finland_sample.csv), from a run in July 2025
- [samples/netherlands_sample.csv](samples/netherlands_sample.csv), from a run in June 2025

| Country | Molecule | Product | Manufacturer | Status | Expected end |
| --- | --- | --- | --- | --- | --- |
| Finland | Riociguat | Adempas 2.5 mg | Abacus Medicine A/S | Shortage ongoing | 15/08/2025 |
| Finland | Ambrisentan | Ambrisentan Accord 10 mg | Paranova Oy | Shortage ongoing | 31/08/2025 |
| Netherlands | Tranylcypromine | Tranylcypromine 10mg tablet, 90 pack | Milstein Cv | Not known (*onbekend*) | Not known |

Personal contact details (names, phone numbers, emails) that the Finnish source includes in its comments have been removed from the sample. A fresh run gives current data, and its format may differ slightly from these older files.

---

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/abdullahsohailcs/eu-drug-shortage-monitor.git
cd eu-drug-shortage-monitor
pip install -r requirements.txt
playwright install chromium
```

Run any scraper:

```bash
python healthcare/drug_shortage_eu/netherlands_scraper.py
```

Each run writes a dated file to `healthcare/drug_shortage_eu/output/`, for example `netherlands_shortages_2026-10-29.csv`. For Belgium, Finland and Portugal, records with missing key fields or scrape errors go to a matching `*_errors_*.xlsx` file.

**Optional settings** (environment variables):

| Variable | Default | What it does |
| --- | --- | --- |
| `OUTPUT_DIR` | `healthcare/drug_shortage_eu/output` | Where output files are saved |
| `REQUEST_DELAY` | `1.5` | Seconds to wait between page requests |

---

## Repository structure

```
eu-drug-shortage-monitor
├── healthcare
│   └── drug_shortage_eu
│       ├── config.py               # shared settings: output folder, request delay
│       ├── belgium_scraper.py
│       ├── finland_scraper.py
│       ├── netherlands_scraper.py
│       ├── spain_scraper.py
│       └── portugal_scraper.py
├── samples                     # 20-row extracts of real output
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Responsible scraping

- Only publicly available data from official sources is collected.
- Requests are spaced out (`REQUEST_DELAY`) to keep the load on these sites low.
- Check each site's terms of use before running these scrapers, and don't use the output in ways those terms or local law don't allow.
- Websites change. If a scraper stops working, the site's layout has probably changed and the selectors need updating.

---

## License

MIT. See [LICENSE](LICENSE).
