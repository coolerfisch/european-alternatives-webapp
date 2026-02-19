import streamlit as st
import requests
import re

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
    # 1. US Vendor Profile
    resp_us = requests.get(f"{REPO_BASE}/{US_VENDOR_FILE}")
    us_profiles = {}
    if resp_us.status_code == 200:
        for b in parse_wild_ts_objects(resp_us.text):
            v_id = extract_field(b, 'id')
            if v_id:
                score = re.search(r'trustScore\s*:\s*(\d+\.?\d*)', b)
                desc_de = re.search(r'descriptionDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                res_matches = re.findall(r'textDe\s*:\s*[\'"`](.*?)[\'"`]', b, re.DOTALL)
                us_profiles[v_id] = {"score": float(score.group(1)) if score else 0.0, "desc": desc_de.group(1) if desc_de else "", "warnings": res_matches}

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

    # 3. Alternativen & Trust Scores
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
                        "id": aid, "name": extract_field(b, 'name'), "country": extract_field(b, 'country'), "category": extract_field(b, 'category'),
                        "desc": de_desc.group(1) if de_desc else extract_field(b, 'description'),
                        "website": extract_field(b, 'website') or extract_field(b, 'url'),
                        "replaces": re.findall(r'[\'"`](.*?)[\'"`]', replaces.group(1)) if replaces else [],
                        "score": eu_scores.get(aid, 0.0)
                    })
    return alternatives, cat_info, us_giant_to_cat, us_profiles

# Daten initial laden
alternatives, cat_info, us_to_cat, us_profiles = load_full_intelligence()

# Session State für Filter initialisieren
if 'filter_cat' not in st.session_state:
    st.session_state.filter_cat = None

# --- UI MAIN ---
st.title("🇪🇺 European Alternatives")
st.markdown("Souveräne Software-Lösungen für dein digitales Leben.")

# Suchfeld (setzt Kategorie-Filter zurück, wenn getippt wird)
query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Gmail, Facebook):", placeholder="Was möchtest du ersetzen?")
if query:
    st.session_state.filter_cat = None

# Kategorien-Buttons (Horizontal)
st.markdown("#### Kategorien durchstöbern")
cat_cols = st.columns(len(list(cat_info.items())[:6]))
for i, (cid, info) in enumerate(list(cat_info.items())[:6]):
    if cat_cols[i].button(f"{info['emoji']} {info['name']}", key=f"btn_{cid}"):
        st.session_state.filter_cat = cid

# Ergebnisse filtern
q = query.lower().strip()
mapped_cat = us_to_cat.get(q)

results = []
if q:
    # Suche hat Vorrang
    results = [a for a in alternatives if q in a['name'].lower() or any(q in r.lower() for r in a['replaces']) or (mapped_cat and a['category'] == mapped_cat)]
elif st.session_state.filter_cat:
    # Button-Filter nutzen
    results = [a for a in alternatives if a['category'] == st.session_state.filter_cat]

# Anzeige der Ergebnisse
if results:
    if q in us_profiles or q == "onedrive":
        profile_key = "microsoft" if q == "onedrive" else q
        if profile_key in us_profiles:
            p = us_profiles[profile_key]
            with st.status(f"⚠️ Risiko-Analyse: {query.capitalize()}", expanded=True):
                st.write(f"**Trust Score:** {p['score']}/10")
                st.write(p['desc'])
                for w in p['warnings'][:2]: st.write(f"• {w}")

    st.subheader(f"🛡️ {len(results)} Treffer gefunden")
    for res in sorted(results, key=lambda x: x['score'], reverse=True):
        with st.container():
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"#### {get_flag(res['country'])} {res['name']}")
            if res['score'] > 0: c2.metric("Trust", res['score'])
            st.write(res['desc'])
            if res['website']: st.link_button(f"🌐 Zu {res['name']}", res['website'])
            st.divider()
elif not q and not st.session_state.filter_cat:
    st.info("Wähle eine Kategorie oder tippe einen US-Dienst ein.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Statistik")
    st.write(f"Dienste geladen: **{len(alternatives)}**")
    
    st.write("---")
    st.header("🔗 Quellen & Code")
    st.markdown("**Datenquelle:** [GitHub Morpheus](https://github.com/TheMorpheus407/european-alternatives)")
    st.markdown("**App-Projekt:** [GitHub coolerfisch](https://github.com/coolerfisch/european-alternatives-webapp/)")
    
    st.write("---")
    st.write("Entwickelt von Martin")
    
    if st.button("🔄 Cache leeren"):
        st.cache_data.clear()
        st.rerun()
