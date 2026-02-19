import streamlit as st
import requests
import json
import re

# --- Konfiguration ---
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

def clean_and_parse_json(text):
    """Extrahiert das JSON-Array aus der TypeScript-Datei."""
    try:
        # Finde den Start des Arrays [ und das Ende ]
        start = text.find('[')
        end = text.rfind(']') + 1
        if start == -1 or end == 0:
            return None
        
        json_data = text[start:end]
        # Entferne potenzielle Trailing Commas, die JSON nicht mag
        json_data = re.sub(r',\s*([\]}])', r'\1', json_data)
        return json.loads(json_data)
    except:
        return None

@st.cache_data(ttl=3600)
def fetch_and_parse_ts():
    all_alternatives = []
    
    for file_name in FILES:
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/src/data/{file_name}"
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                continue
            
            # 1. Versuch: Sauberes JSON-Parsing (für die generierten Dateien)
            data = clean_and_parse_json(resp.text)
            
            if data and isinstance(data, list):
                for item in data:
                    # Extrahiere die deutschen Details, falls vorhanden
                    desc = item.get("localizedDescriptions", {}).get("de", "")
                    if not desc:
                        desc = item.get("description", "Keine Beschreibung verfügbar.")
                    
                    all_alternatives.append({
                        "name": item.get("name", "Unbekannt"),
                        "replaces": ", ".join(item.get("replacesUS", [])),
                        "description": desc,
                        "url": item.get("website", "")
                    })
            else:
                # 2. Fallback: Robuster Regex-Parser (für handgeschriebene Dateien)
                text = resp.text
                blocks = re.findall(r'\{[\s\S]*?\}', text)
                for block in blocks:
                    name_m = re.search(r'"name"\s*:\s*"(.*?)"', block)
                    if not name_m: continue
                    
                    reps_m = re.search(r'"replacesUS"\s*:\s*\[([\s\S]*?)\]', block)
                    replaces = ", ".join(re.findall(r'"(.*?)"', reps_m.group(1))) if reps_m else ""
                    
                    url_m = re.search(r'"website"\s*:\s*"(.*?)"', block)
                    
                    all_alternatives.append({
                        "name": name_m.group(1),
                        "replaces": replaces,
                        "description": "Details im Hauptkatalog verfügbar.",
                        "url": url_m.group(1) if url_m else ""
                    })
                    
        except Exception:
            continue
            
    return all_alternatives

# --- User Interface ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Suche nach europäischen Alternativen (Datenstand: Februar 2026)")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Welchen US-Dienst möchtest du ersetzen?", placeholder="z.B. OneDrive, Outlook, LastPass...")

    if query:
        q = query.lower().strip()
        results = [d for d in data if q in d["name"].lower() or q in d["replaces"].lower()]
        
        if results:
            st.success(f"{len(results)} Treffer gefunden:")
            for r in results:
                with st.container():
                    st.markdown(f"### {r['name']}")
                    if r['replaces']:
                        st.write(f"**Ersetzt:** {r['replaces']}")
                    st.write(f"**Details:** {r['description']}")
                    
                    if r['url']:
                        st.link_button(f"🌐 Zu {r['name']}", r['url'])
                    st.divider()
        else:
            st.info(f"Kein Treffer für '{query}'. Tipp: Versuche es mit 'Cloud', 'Email' oder 'Office'.")

with st.sidebar:
    st.header("Statistik")
    st.write(f"Dienste im Katalog: **{len(data)}**")
    st.write("---")
    st.markdown("[App-Quellcode](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Status: Live-Daten-Anbindung aktiv.")
