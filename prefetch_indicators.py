# prefetch_indicators.py
"""
Prefetch World Bank indicators for ALL countries and save as CSVs.
Run once before demo to make app instant for all countries.
"""

import requests
import pandas as pd
import time
import os
from tqdm import tqdm

os.makedirs("data/prefetched", exist_ok=True)

INDICATORS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita": "NY.GDP.PCAP.KD",
    "exports_pct_gdp": "NE.EXP.GNFS.ZS",
}

def fetch_wb_countries():
    url = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    r = requests.get(url, timeout=30)
    j = r.json()
    countries = pd.DataFrame(j[1])
    countries = countries[['id','iso2Code','name','region','incomeLevel']]
    countries.columns = ['id','iso2','name','region','incomeLevel']
    return countries

def fetch_indicator_for_all(indicator_code):
    per_page = 1000
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page={per_page}"
    r = requests.get(url, timeout=60)
    j = r.json()
    if not isinstance(j, list) or len(j) < 2:
        return pd.DataFrame()
    total = int(j[0].get('total', 0))
    pages = int(j[0].get('pages', 1))
    rows = []
    for p in tqdm(range(1, pages+1), desc=f"Pages for {indicator_code}"):
        urlp = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page={per_page}&page={p}"
        rp = requests.get(urlp, timeout=60)
        jp = rp.json()
        if isinstance(jp, list) and len(jp) >= 2:
            rows.extend(jp[1])
        time.sleep(0.2)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['iso2'] = df['country'].apply(lambda c: c.get('id') if isinstance(c, dict) else None)
    df['country_name'] = df['country'].apply(lambda c: c.get('value') if isinstance(c, dict) else None)
    df = df[['iso2','countryiso3code','country_name','date','value']]
    return df

def latest_by_country(df):
    df = df.dropna(subset=['value'])
    df['date_int'] = df['date'].astype(int)
    df_sorted = df.sort_values(['iso2','date_int'], ascending=[True, False])
    latest = df_sorted.groupby('iso2').first().reset_index()
    return latest[['iso2','country_name','countryiso3code','date','value']]

def main():
    print("Fetching country list from World Bank...")
    countries = fetch_wb_countries()
    countries.to_csv("data/prefetched/wb_countries.csv", index=False)
    print(f"Got {len(countries)} countries.")

    for key, indicator in INDICATORS.items():
        print(f"Fetching indicator {key} ({indicator}) for all countries...")
        df = fetch_indicator_for_all(indicator)
        if df.empty:
            print("Warning: empty response for", indicator)
            continue
        latest = latest_by_country(df)
        latest.to_csv(f"data/prefetched/wb_{key}.csv", index=False)
        print(f"Wrote data/prefetched/wb_{key}.csv ({len(latest)} rows).")
        time.sleep(0.5)

    print("Prefetch complete. Files in data/prefetched/")
    print("Files:", os.listdir("data/prefetched"))

if __name__ == "__main__":
    main()

