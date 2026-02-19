import streamlit as st
import requests
import re

# --- Konfiguration ---
REPO_BASE = "https://raw.githubusercontent.com/TheMorpheus407/european-alternatives/main/src/data"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]
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
def load_data():
    # 1. US Vendor Profile (für Risiko-Analyse)
    resp_us = requests.get(f"{REPO_BASE}/{US_VENDOR_FILE}")
    us_profiles = {}
    if resp_us.status_code == 200:
        blocks = parse_wild_ts_objects(resp_us.text)
        for b in blocks:
            v_id = extract_field(b, 'id')
            if v_id:
                score = re.search(r'trustScore\s*:\s*(\d+\.?\d*)', b)
                desc_de = re.search(r'descriptionDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                res_matches = re.findall(r'textDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                us_profiles[v_id] = {
                    "score": float(score.group(1)) if score else 0.0,
                    "desc": desc_de.group(1) if desc_de else "",
                    "warnings": res_matches
                }

    # 2. Trust Scores der europäischen Alternativen
    resp_trust = requests.get(f"{REPO_BASE}/{TRUST_FILE}")
    eu_scores = {m[0]: float(m[1]) for m in re.findall(r'[\'"]?([\w-]+)[\'"]?\s*:\s*(\d+\.?\d*)', resp_trust.text)} if resp_trust.status_code == 200 else {}
    
    # 3. Die Alternativen selbst
    alternatives = []
    ids_seen = set()
    for f in FILES:
        resp = requests.get(f"{REPO_BASE}/{f}")
        if resp.status_code == 200:
            for b in parse_wild_ts_objects(resp.text):
                aid = extract_field(b, 'id')
                if aid and aid not in ids_seen:
                    de_desc = re.search(r'de\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                    replaces = re.search(r'replacesUS\s*:\s*\[(.*?)\]', b, re.DOTALL)
                    alternatives.append({
                        "id": aid,
                        "name": extract_field(b, 'name'),
                        "country": extract_field(b, 'country'),
                        "desc": de_desc.group(1) if de_desc else extract_field(b, 'description'),
                        "website": extract_field(b, 'website') or extract_field(b, 'url'),
                        "replaces": re.findall(r'[\'"`](.*?)[\'"`]', replaces.group(1)) if replaces else [],
                        "score": eu_scores.get(aid, 0.0)
                    })
                    ids_seen.add(aid)
    return alternatives, us_profiles

# Daten laden
alternatives, us_profiles = load_data()

# --- UI MAIN ---
st.title("🇪🇺 European Alternatives")
st.markdown("Souveräne Software-Lösungen für dein digitales Leben.")

query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Gmail, Facebook):", placeholder="Was möchtest du ersetzen?")

if query:
    q = query.lower().strip()
    
    # Risiko-Analyse (Mapping OneDrive -> Microsoft)
    profile_key = "microsoft" if q == "onedrive" else q
    if profile_key in us_profiles:
        p = us_profiles[profile_key]
        with st.status(f"⚠️ Risiko-Analyse: {query.capitalize()}", expanded=True):
            st.write(f"**Trust Score:** {p['score']}/10")
            st.write(p['desc'])
            if p['warnings']:
                st.markdown("**Bekannte Probleme:**")
                for w in p['warnings'][:3]: st.write(f"• {w}")

    # Ergebnisse filtern
    results = [a for a in alternatives if q in a['name'].lower() or any(q in r.lower() for r in a['replaces'])]

    if results:
        st.subheader("🛡️ Empfohlene europäische Lösungen")
        for res in sorted(results, key=lambda x: x['score'], reverse=True):
            with st.container():
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"#### {get_flag(res['country'])} {res['name']}")
                if res['score'] > 0: c2.metric("Trust", res['score'])
                st.write(res['desc'])
                if res['website']: st.link_button(f"🌐 Zu {res['name']}", res['website'])
                st.divider()
    else:
        st.info("Keine direkten Treffer gefunden.")
else:
    st.info("Tippe oben einen US-Dienst ein, um europäische Alternativen zu finden.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Statistik")
    st.write(f"Dienste geladen: **{len(alternatives)}**")
    
    st.write("---")
    st.header("🔗 Quellen & Code")
    st.markdown("**Datenquelle:**")
    st.markdown("[GitHub: TheMorpheus407 / European Alternatives](https://github.com/TheMorpheus407/european-alternatives)")
    
    st.markdown("**App-Projekt:**")
    st.markdown("[GitHub: coolerfisch / Web-App](https://github.com/coolerfisch/european-alternatives-webapp/)")
    
    st.write("---")
    st.write("Entwickelt von Martin")
    
    if st.button("🔄 Cache aktualisieren"):
        st.cache_data.clear()
        st.rerun()
