import streamlit as st
import requests
import re
import json

# Neue Pfade basierend auf deiner src-Struktur
REPO_BASE = "https://raw.githubusercontent.com/TheMorpheus407/european-alternatives/main/src/data/"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

@st.cache_data(ttl=3600)
def fetch_ts_data():
    all_alternatives = []
    for file_name in FILES:
        url = REPO_BASE + file_name
        resp = requests.get(url)
        if resp.status_code == 200:
            # Extrahiere den Inhalt zwischen den eckigen Klammern [ ... ]
            # Da es TS ist, nutzen wir einen groben Regex-Match für die Objekte
            content = resp.text
            # Suche nach Objekten wie { name: "...", replaces: "..." }
            matches = re.findall(r'\{[\s\S]*?\}', content)
            for m in matches:
                # Bereinigen der TS-Syntax zu fast-JSON
                clean = m.replace('name:', '"name":').replace('replaces:', '"replaces":').replace('description:', '"description":').replace('url:', '"url":').replace("'", '"')
                try:
                    # Versuche es als Dictionary zu laden (vereinfacht)
                    name = re.search(r'name:\s*["\'](.*?)["\']', m)
                    replaces = re.search(r'replaces:\s*\[(.*?)\]', m)
                    desc = re.search(r'description:\s*["\'](.*?)["\']', m)
                    
                    if name:
                        all_alternatives.append({
                            "name": name.group(1),
                            "replaces": replaces.group(1) if replaces else "",
                            "description": desc.group(1) if desc else ""
                        })
                except:
                    continue
    return all_alternatives

st.title("Digitaler Souveraenitaets-Check")
st.write("Live-Abfrage der src/data Komponenten")

data = fetch_ts_data()

query = st.text_input("Suche nach US-Dienst:", placeholder="z.B. WhatsApp")

if query:
    q = query.lower()
    results = [d for d in data if q in d["replaces"].lower() or q in d["name"].lower()]
    
    if results:
        for r in results:
            st.success(f"Empfehlung: {r['name']}")
            st.write(f"Ersetzt: {r['replaces']}")
            st.write(r['description'])
            st.divider()
    else:
        st.info("Kein Treffer in den TS-Datenquellen gefunden.")

with st.sidebar:
    st.write("Projekt: European Alternatives")
    st.write("Quelle: src/data/ (TypeScript Dataset)")
    st.write("Status: coolerfisch UI")
