# app.py
"""
YKMarketShift — Streamlit single-file app (robust, global)
- Fixes earlier KeyErrors
- All-country selector using RestCountries (fallback to embedded)
- Builds per-country profiles on-demand with safe defaults
- Exchange-rate pricing calc + PDF export
- Offline fallback dataset included for demo-proofing
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="YKMarketShift", layout="wide", initial_sidebar_state="expanded")

# --------------------------
# Embedded fallback dataset (small curated snapshot for quick demo)
# --------------------------
FALLBACK = [
    {"country":"China","iso3":"CHN","population":1411778724,"gdp_growth":4.5,"exports_pct_gdp":18.0,"gdp_per_capita":12000,"logistics":3.3,"gii":50.1,"epi":60.2,"currency":"CNY"},
    {"country":"India","iso3":"IND","population":1410000000,"gdp_growth":6.7,"exports_pct_gdp":12.3,"gdp_per_capita":2500,"logistics":3.0,"gii":35.4,"epi":42.1,"currency":"INR"},
    {"country":"Vietnam","iso3":"VNM","population":98168229,"gdp_growth":6.1,"exports_pct_gdp":100.5,"gdp_per_capita":3200,"logistics":3.4,"gii":30.5,"epi":50.9,"currency":"VND"},
    {"country":"Mexico","iso3":"MEX","population":128932753,"gdp_growth":2.1,"exports_pct_gdp":38.6,"gdp_per_capita":9800,"logistics":3.6,"gii":39.0,"epi":64.3,"currency":"MXN"},
    {"country":"United States","iso3":"USA","population":331893745,"gdp_growth":2.3,"exports_pct_gdp":11.5,"gdp_per_capita":65000,"logistics":4.0,"gii":60.7,"epi":71.2,"currency":"USD"}
]
FALLBACK_DF = pd.DataFrame(FALLBACK).set_index('country')

# --------------------------
# API constants
# --------------------------
WORLD_BANK_INDICATORS = {
    "gdp_growth":"NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita":"NY.GDP.PCAP.KD",
    "exports_pct_gdp":"NE.EXP.GNFS.ZS",
}

EXCHANGE_FALLBACK = {"USD":1.0, "INR":83.0, "CNY":7.2, "VND":24000.0, "MXN":17.0, "EUR":0.92}

# --------------------------
# Cached network calls (best-effort)
# --------------------------
@st.cache_data(ttl=60*60)
def fetch_restcountries_df():
    url = "https://restcountries.com/v3.1/all"
    try:
        r = requests.get(url, timeout=6)
        js = r.json()
        rows = []
        for c in js:
            name = c.get('name',{}).get('common')
            iso3 = c.get('cca3', None)
            pop = c.get('population', None)
            cur = None
            try:
                cur_keys = list(c.get('currencies', {}).keys())
                cur = cur_keys[0] if cur_keys else None
            except:
                cur = None
            if name:
                rows.append({"country":name,"iso3":iso3,"population":pop,"currency":cur})
        df = pd.DataFrame(rows).dropna(subset=['country']).reset_index(drop=True)
        return df
    except Exception:
        return None

@st.cache_data(ttl=60*60)
def worldbank_indicator_series(iso, indicator):
    try:
        url = f"https://api.worldbank.org/v2/country/{iso}/indicator/{indicator}?format=json&per_page=200"
        r = requests.get(url, timeout=8)
        j = r.json()
        if isinstance(j, list) and len(j) >= 2:
            df = pd.DataFrame(j[1])
            df = df[['date','value']].dropna()
            df['date'] = df['date'].astype(int)
            return df.sort_values('date')
    except Exception:
        pass
    return pd.DataFrame(columns=['date','value'])

@st.cache_data(ttl=60*60)
def fetch_exchange_rates(base="USD"):
    try:
        r = requests.get(f"https://api.exchangerate.host/latest?base={base}", timeout=6)
        j = r.json()
        return j.get("rates", {})
    except Exception:
        return {}

# --------------------------
# Heuristics: risk scoring and PDF generation
# --------------------------
def compute_risk(profile, weights=None):
    if weights is None:
        weights = {"exports":0.35,"growth":0.25,"logistics":0.25,"gdp_pc":0.15}
    exp = profile.get('exports_pct_gdp', 20) / 100.0
    growth = max(min((5 - profile.get('gdp_growth',3))/10,1),0)
    logistics = max(min((5 - profile.get('logistics',3))/4,1),0)
    gdp_pc_norm = 1 - np.tanh(profile.get('gdp_per_capita',10000)/50000)
    raw = (weights['exports']*exp) + (weights['growth']*growth) + (weights['logistics']*logistics) + (weights['gdp_pc']*gdp_pc_norm)
    score = int(np.clip(raw*100, 1, 99))
    return score

import unicodedata

def sanitize_for_pdf(s: str) -> str:
    """
    Convert unicode text to plain ASCII-friendly text for PyFPDF (latin-1).
    Removes/normalizes characters that PyFPDF can't encode.
    """
    if s is None:
        return ""
    # Normalize to NFKD (separate accents), then drop non-ASCII.
    normalized = unicodedata.normalize("NFKD", s)
    ascii_bytes = normalized.encode("ascii", "ignore")  # drops non-ascii
    # Replace multiple consecutive spaces/newlines, preserve readability
    text = ascii_bytes.decode("ascii")
    # Convert fancy dashes/quotes in remaining (if any) to simple ones
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text

def generate_pdf(brief_text, country_name, footer_line="Built by Yatin - YKMarketShift"):
    """
    Generate a one-page PDF (FPDF) from plain text.
    We sanitize text to avoid PyFPDF latin-1 encoding errors.
    """
    pdf = FPDF(format='A4', unit='mm')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=14, style='B')

    title = f"Market Entry Brief - {country_name}"
    pdf.cell(0, 8, sanitize_for_pdf(title), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", size=10)

    safe_text = sanitize_for_pdf(brief_text)
    for line in safe_text.split('\n'):
        # ensure we don't feed extremely long single lines (wrap)
        pdf.multi_cell(0, 6, line)

    pdf.ln(6)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 6, sanitize_for_pdf(footer_line), ln=True)

    b = pdf.output(dest='S').encode('latin-1')  # safe now
    return b


# --------------------------
# Profile builder (on-demand) — robust defaults and safe returns
# --------------------------
@st.cache_data(ttl=60*60)
def build_profile_for_country(country_name):
    # Always return a dict with required keys
    profile = {
        "country": country_name,
        "iso3": None,
        "population": None,
        "gdp_growth": None,
        "exports_pct_gdp": None,
        "gdp_per_capita": None,
        "logistics": 3.0,
        "gii": 30.0,
        "epi": 50.0,
        "currency": "USD",
    }

    # Try fallback first
    if country_name in FALLBACK_DF.index:
        fb = FALLBACK_DF.loc[country_name].to_dict()
        for k,v in fb.items():
            profile[k] = v

    # Enrich from RestCountries if possible
    rest_df = fetch_restcountries_df()
    if rest_df is not None and country_name in rest_df['country'].values:
        rrow = rest_df[rest_df['country']==country_name].iloc[0]
        profile['iso3'] = profile.get('iso3') or rrow.get('iso3')
        profile['population'] = int(profile.get('population') or (rrow.get('population') or 0))
        profile['currency'] = profile.get('currency') or rrow.get('currency') or "USD"

    iso = (profile.get('iso3') or "").lower()
    if iso:
        # Try to fetch latest indicators (best-effort)
        try:
            df_g = worldbank_indicator_series(iso, WORLD_BANK_INDICATORS['gdp_growth'])
            if not df_g.empty:
                profile['gdp_growth'] = float(df_g['value'].dropna().tail(1).values[0])
        except:
            pass
        try:
            df_exp = worldbank_indicator_series(iso, WORLD_BANK_INDICATORS['exports_pct_gdp'])
            if not df_exp.empty:
                profile['exports_pct_gdp'] = float(df_exp['value'].dropna().tail(1).values[0])
        except:
            pass
        try:
            df_pc = worldbank_indicator_series(iso, WORLD_BANK_INDICATORS['gdp_per_capita'])
            if not df_pc.empty:
                profile['gdp_per_capita'] = float(df_pc['value'].dropna().tail(1).values[0])
        except:
            pass

    # Finalize sensible defaults if still missing
    if profile.get('gdp_growth') is None:
        profile['gdp_growth'] = 3.0
    if profile.get('exports_pct_gdp') is None:
        profile['exports_pct_gdp'] = 20.0
    if profile.get('gdp_per_capita') is None:
        profile['gdp_per_capita'] = 5000.0
    if profile.get('population') is None:
        profile['population'] = 1_000_000

    # compute risk
    profile['risk_score'] = compute_risk(profile, weights=None)
    return profile

# --------------------------
# Sidebar UI: history & priorities
# --------------------------
st.sidebar.title("YKMarketShift")
st.sidebar.markdown("Instant country compare — no login, demo-safe.")

# Build global country list from RestCountries (fallback to embedded)
rest_df = fetch_restcountries_df()
if rest_df is not None:
    all_country_list = sorted(rest_df['country'].tolist())
else:
    all_country_list = FALLBACK_DF.index.tolist()

selected = st.sidebar.multiselect("Select up to 4 countries", options=all_country_list, default=["China","India","Vietnam"])
if len(selected) == 0:
    selected = ["China","India"]

priority_cost = st.sidebar.slider("Weight: Cost (lower labor / gdp per capita)", 0, 100, 40)
priority_risk = st.sidebar.slider("Weight: Risk (supply concentration / politics)", 0, 100, 30)
priority_logistics = st.sidebar.slider("Weight: Logistics (ports, LPI proxy)", 0, 100, 20)
priority_green = st.sidebar.slider("Weight: Sustainability/Innovation (EPI / GII)", 0, 100, 10)

# Pricing / FX in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("Pricing / FX demo")
base_price = st.sidebar.number_input("Unit price in USD (example)", min_value=0.0, value=10.0, step=0.5, format="%.2f")
currency_base = st.sidebar.selectbox("Price denominator currency (base)", options=["USD","EUR"], index=0)
st.sidebar.markdown("Note: API fallback used if internet is flaky.")

# fetch exchange rates (cached)
rates = fetch_exchange_rates(base=currency_base)
if not rates:
    rates = EXCHANGE_FALLBACK

# --------------------------
# Build profiles list robustly
# --------------------------
profiles = []
for c in selected:
    try:
        p = build_profile_for_country(c)
        if not isinstance(p, dict):
            # defensive fallback
            p = {"country": c, "gdp_per_capita":5000.0, "gdp_growth":3.0, "exports_pct_gdp":20.0, "logistics":3.0, "risk_score": compute_risk({"gdp_per_capita":5000.0,"gdp_growth":3.0,"exports_pct_gdp":20.0,"logistics":3.0})}
        # ensure 'country' key present
        if 'country' not in p:
            p['country'] = c
        profiles.append(p)
    except Exception as e:
        # if building failed, append a safe default profile
        p = {"country": c, "gdp_per_capita":5000.0, "gdp_growth":3.0, "exports_pct_gdp":20.0, "logistics":3.0, "risk_score": compute_risk({"gdp_per_capita":5000.0,"gdp_growth":3.0,"exports_pct_gdp":20.0,"logistics":3.0})}
        profiles.append(p)

# Safe DataFrame creation — ensure at least one dict
if len(profiles) == 0:
    profiles = [build_profile_for_country("India")]

profiles_df = pd.DataFrame(profiles)
if 'country' not in profiles_df.columns:
    # ensure there is a country column, possibly use index from selection
    profiles_df['country'] = selected
profiles_df = profiles_df.set_index('country')

# --------------------------
# Header / top summary cards
# --------------------------
st.title("YKMarketShift — Country Compare & China-Plus-One Advisor")
st.markdown("A single-file, professor-ready tool. Live APIs used when available; embedded fallback ensures demo reliability.")

cols = st.columns(len(profiles_df))
for col, (name, row) in zip(cols, profiles_df.iterrows()):
    with col:
        st.markdown(f"### {name}")
        st.metric(label="Risk Score (0-100)", value=int(row.get('risk_score', 0)))
        st.write(f"GDP growth (latest): **{float(row.get('gdp_growth',0)):.2f}%**")
        st.write(f"Exports %GDP: **{float(row.get('exports_pct_gdp',0)):.1f}%**")
        st.write(f"Logistics proxy: **{float(row.get('logistics',3)):.2f}**")
        st.write(f"GDP per capita: **${int(row.get('gdp_per_capita',0)):,}**")

# --------------------------
# Trade-off plot
# --------------------------
st.subheader("Trade-off: Risk vs Cost (interactive)")
def combined_score_row(r):
    cost = 1 - np.tanh(float(r.get('gdp_per_capita',10000))/50000)
    risk = float(r.get('risk_score',50))/100.0
    cw = priority_cost/ (priority_cost+priority_risk+1e-9)
    rw = priority_risk/ (priority_cost+priority_risk+1e-9)
    return cw*cost + rw*risk

scatter_df = profiles_df.copy()
scatter_df['combined'] = scatter_df.apply(lambda r: combined_score_row(r.to_dict()), axis=1)
fig = px.scatter(scatter_df.reset_index(), x='gdp_per_capita', y='risk_score', size='exports_pct_gdp',
                 hover_name='country', labels={'gdp_per_capita':'GDP per capita (USD)','risk_score':'Risk (0-100)'},
                 title="Countries: lower-right is ideal (low risk, low cost)")
st.plotly_chart(fig, use_container_width=True)

# --------------------------
# China-Plus-One advisor
# --------------------------
st.subheader("China-Plus-One Advisor")
for name in profiles_df.index:
    p = profiles_df.loc[name].to_dict()
    cost_idx = 1 - np.tanh(float(p.get('gdp_per_capita',5000))/50000)
    suitability = (priority_cost/100)*(1-cost_idx) + (priority_risk/100)*(1 - (float(p.get('risk_score',50))/100)) + (priority_logistics/100)*(float(p.get('logistics',3))/5)
    profiles_df.loc[name,'suitability'] = suitability

recommendation = profiles_df.sort_values('suitability', ascending=False).iloc[0]
st.markdown(f"**Top pick:** {recommendation.name} — Suitability score: **{recommendation.suitability:.2f}**")
st.write("Explainable breakdown:")
st.write(f"- Exports %GDP: {recommendation.exports_pct_gdp:.1f}%  \n- GDP per capita: ${int(recommendation.gdp_per_capita):,}  \n- Logistics proxy: {recommendation.logistics:.2f}  \n- Risk (base): {int(recommendation.risk_score)}")

# --------------------------
# Curated case studies
# --------------------------
st.subheader("Curated Case Studies (one-click)")
case_presets = {
    "Apple - iPhone assembly (cost + scale)": {"countries":["China","Vietnam","India","Mexico"], "cost":50,"risk":20,"logistics":20},
    "Nike - Apparel (fast fashion speed)": {"countries":["Vietnam","India","Bangladesh","China"], "cost":50,"risk":30,"logistics":20},
    "Automotive EV parts (quality + proximity to US)": {"countries":["Mexico","China","India","Vietnam"], "cost":30,"risk":30,"logistics":40}
}
cs = st.selectbox("Pick a case study", options=list(case_presets.keys()))
if cs:
    st.write("Preset:", cs)
    preset = case_presets[cs]
    st.write("Preset priorities — use these verbally in class:")
    st.write(f"Cost: {preset['cost']}, Risk: {preset['risk']}, Logistics: {preset['logistics']}")
    temp_scores = {}
    for c in preset['countries']:
        # build profile robustly (ensures risk_score exists)
        p = build_profile_for_country(c)
        # ensure numeric defaults
        p['gdp_per_capita'] = float(p.get('gdp_per_capita', 5000.0))
        p['gdp_growth'] = float(p.get('gdp_growth', 3.0))
        p['exports_pct_gdp'] = float(p.get('exports_pct_gdp', 20.0))
        p['logistics'] = float(p.get('logistics', 3.0))
        if 'risk_score' not in p:
            p['risk_score'] = compute_risk(p, weights=None)
        cost_idx = 1 - np.tanh(p['gdp_per_capita']/50000)
        suitability = (preset['cost']/100)*(1-cost_idx) + (preset['risk']/100)*(1 - (p['risk_score']/100)) + (preset['logistics']/100)*(p['logistics']/5)
        temp_scores[c] = suitability
    if temp_scores:
        ranked = sorted(temp_scores.items(), key=lambda x: x[1], reverse=True)
        st.write("Ranking (best → worst):")
        for r,s in ranked:
            st.write(f"- {r}: {s:.2f}")

# --------------------------
# Exchange-rate pricing calculator
# --------------------------
st.subheader("Exchange Rate Pricing Calculator")
st.write("Show how currency moves change unit cost in local currency (live rates, fallback used if offline).")

available_currencies = sorted({v.get('currency') for v in FALLBACK if v.get('currency')}) + ["USD","EUR"]
available_currencies = list(dict.fromkeys(available_currencies))
target_currency = st.selectbox("Convert unit price to (currency)", options=available_currencies, index=available_currencies.index("INR") if "INR" in available_currencies else 0)

# determine rate
try:
    if target_currency == currency_base:
        rate = 1.0
    else:
        rate = rates.get(target_currency, None)
        if rate is None:
            rate = EXCHANGE_FALLBACK.get(target_currency, EXCHANGE_FALLBACK.get("INR", 83.0))
except:
    rate = EXCHANGE_FALLBACK.get(target_currency, EXCHANGE_FALLBACK.get("INR", 83.0))

st.write(f"Live rate (approx): 1 {currency_base} = {rate:.4f} {target_currency}")
local_unit = base_price * rate
st.metric(label=f"Unit price in {target_currency}", value=f"{local_unit:,.2f} {target_currency}")

pct = 0.05
up = base_price * (rate*(1+pct))
down = base_price * (rate*(1-pct))
st.write(f"If {currency_base} weakens by 5% → unit = {up:,.2f} {target_currency}")
st.write(f"If {currency_base} strengthens by 5% → unit = {down:,.2f} {target_currency}")

# --------------------------
# Download brief (TXT + PDF)
# --------------------------
st.subheader("Download: One-page Market Entry brief (TXT + PDF)")
selected_for_brief = st.selectbox("Choose country for short brief", options=profiles_df.index.tolist(), key="brief_select")
if selected_for_brief:
    r = profiles_df.loc[selected_for_brief].to_dict()
    brief_text = f"""Market Entry Brief — {selected_for_brief}
Date: {datetime.utcnow().date().isoformat()}

Key stats:
- GDP growth (latest): {r['gdp_growth']:.2f}%
- Exports % GDP: {r['exports_pct_gdp']:.1f}%
- Logistics proxy: {r['logistics']:.2f}
- GDP per capita: ${int(r['gdp_per_capita']):,}
- Risk score (0-100): {int(r['risk_score'])}

Pricing example (unit price):
- Base unit price: {base_price:.2f} {currency_base}
- Approx local unit price: {local_unit:,.2f} {target_currency}

Recommended position for manufacturing/sourcing:
- Suitability (given your priorities): {r['suitability']:.2f}
- Short rationale: Balanced between cost & risk. Use local partners and check IP and tariff implications.

Professor note: This brief is generated using public World Bank/RestCountries proxies and heuristics. For procurement-grade decisions, complement with firm-level TCO & verified tariff tables.
"""
    st.code(brief_text)
    st.download_button("Download brief (TXT)", data=brief_text.encode('utf-8'),
                       file_name=f"market_entry_brief_{selected_for_brief}.txt")
    pdf_bytes = generate_pdf(brief_text, selected_for_brief, footer_line="Built by Yatin — YKMarketShift (demo-only)")
    st.download_button("Download brief (PDF)", data=pdf_bytes, file_name=f"market_entry_brief_{selected_for_brief}.pdf", mime="application/pdf")

st.markdown("---")
st.caption("Built by Yatin (YKMarketShift). Demo-safe: embedded dataset used if live APIs fail. Keep this secret for your live presentation 😉")