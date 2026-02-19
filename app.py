import streamlit as st
import requests
import re
import json

# --- Konfiguration ---
REPO_BASE = "https://raw.githubusercontent.com/TheMorpheus407/european-alternatives/main/src/data"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]
CAT_FILE = "categories.ts"
TRUST_FILE = "trustOverrides.ts"
US_VENDOR_FILE = "usVendors.ts"

st.set_page_config(page_title="EU Alternative Navigator", layout="wide", page_icon="🇪🇺")

# --- Hilfsfunktionen ---
def get_flag(country_code):
    flags = {"de": "🇩🇪", "ch": "🇨🇭", "at": "🇦🇹", "fr": "🇫🇷", "gb": "🇬🇧", "nl": "🇳🇱", "ee": "🇪🇪", "no": "🇳🇴", "it": "🇮🇹", "be": "🇧🇪", "lu": "🇱🇺", "es": "🇪🇸", "pl": "🇵🇱", "se": "🇸🇪", "cz": "🇨🇿", "eu": "🇪🇺", "ca": "🇨🇦", "us": "🇺🇸"}
    return flags.get(country_code.lower(), "🌐")

def parse_wild_ts_objects(text):
    """Extrahiert Objekte aus TS/JSON mit Klammer-Zähler."""
    objects, depth, current = [], 0, []
    for char in text:
        if char == '{': depth += 1
        if depth > 0: current.append(char)
        if char == '}':
            depth -= 1
            if depth == 0:
                objects.append("".join(current))
                current = []
    return objects

def extract_field(block, field_name):
    pattern = rf'{field_name}\s*:\s*[\'"`](.*?)[\'"`]'
    m = re.search(pattern, block, re.DOTALL)
    return m.group(1).strip() if m else ""

# --- Daten-Loader ---
@st.cache_data(ttl=3600)
def load_full_intelligence():
    # 1. US Vendors & Profiles laden
    resp_us = requests.get(f"{REPO_BASE}/{US_VENDOR_FILE}")
    us_profiles = {}
    if resp_us.status_code == 200:
        blocks = parse_wild_ts_objects(resp_us.text)
        for b in blocks:
            v_id = extract_field(b, 'id')
            if v_id:
                score = re.search(r'trustScore\s*:\s*(\d+\.?\d*)', b)
                desc_de = re.search(r'descriptionDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                us_profiles[v_id] = {
                    "score": float(score.group(1)) if score else 0.0,
                    "desc": desc_de.group(1) if desc_de else "",
                    "warnings": []
                }
                # Warnungen (Reservations) für US-Anbieter ziehen
                res_matches = re.findall(r'textDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                us_profiles[v_id]["warnings"] = res_matches

    # 2. Kategorien & US-Giant Mapping
    resp_cat = requests.get(f"{REPO_BASE}/{CAT_FILE}")
    us_giant_to_cat, cat_info = {}, {}
    if resp_cat.status_code == 200:
        for b in parse_wild_ts_objects(resp_cat.text):
            cid = extract_field(b, 'id')
            if cid:
                cat_info[cid] = {"name": extract_field(b, 'name'), "emoji": extract_field(b, 'emoji')}
                giants = re.search(r'usGiants\s*:\s*\[(.*?)\]', b, re.DOTALL)
                if giants:
                    for g in re.findall(r'[\'"`](.*?)[\'"`]', giants.group(1)):
                        us_giant_to_cat[g.lower()] = cid

    # 3. Europäische Alternativen & Trust Scores
    resp_trust = requests.get(f"{REPO_BASE}/{TRUST_FILE}")
    eu_scores = {m[0]: float(m[1]) for m in re.findall(r'[\'"]?([\w-]+)[\'"]?\s*:\s*(\d+\.?\d*)', resp_trust.text)} if resp_trust.status_code == 200 else {}
    
    alternatives = []
    for f in FILES:
        resp = requests.get(f"{REPO_BASE}/{f}")
        if resp.status_code == 200:
            for b in parse_wild_ts_objects(resp.text):
                aid = extract_field(b, 'id')
                if aid:
                    de_desc = re.search(r'de\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                    replaces = re.search(r'replacesUS\s*:\s*\[(.*?)\]', b, re.DOTALL)
                    alternatives.append({
                        "id": aid, "name": extract_field(b, 'name'),
                        "country": extract_field(b, 'country'), "category": extract_field(b, 'category'),
                        "desc": de_desc.group(1) if de_desc else extract_field(b, 'description'),
                        "website": extract_field(b, 'website') or extract_field(b, 'url'),
                        "replaces": re.findall(r'[\'"`](.*?)[\'"`]', replaces.group(1)) if replaces else [],
                        "score": eu_scores.get(aid, 0.0)
                    })
    return alternatives, cat_info, us_giant_to_cat, us_profiles

# Daten laden
alternatives, cat_info, us_to_cat, us_profiles = load_full_intelligence()

# --- UI ---
st.title("🇪🇺 European Alternatives")
query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Gmail, Facebook):", placeholder="Was möchtest du ersetzen?")

if query:
    q = query.lower().strip()
    mapped_cat = us_to_cat.get(q)
    
    # Anzeige des US-Profils (falls vorhanden)
    if q in us_profiles or q == "onedrive": # OneDrive Mapping auf Microsoft Profile
        profile_key = "microsoft" if q == "onedrive" else q
        if profile_key in us_profiles:
            p = us_profiles[profile_key]
            with st.status(f"⚠️ Risiko-Analyse: {query.capitalize()}", expanded=True):
                st.write(f"**Trust Score:** {p['score']}/10")
                st.write(p['desc'])
                for w in p['warnings'][:3]: st.write(f"• {w}")

    # Alternativen filtern
    results = [a for a in alternatives if q in a['name'].lower() or any(q in r.lower() for r in a['replaces']) or (mapped_cat and a['category'] == mapped_cat)]

    if results:
        st.subheader("🛡️ Empfohlene europäische Lösungen")
        for res in sorted(results, key=lambda x: x['score'], reverse=True):
            with st.container():
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"#### {get_flag(res['country'])} {res['name']}")
                if res['score'] > 0: c2.metric("Trust", res['score'])
                st.write(res['desc'])
                if res['website']: st.link_button(f"Zu {res['name']}", res['website'])
                st.divider()
