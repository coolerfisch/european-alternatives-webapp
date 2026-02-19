import streamlit as st
import requests
import re

# Konfiguration
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

@st.cache_data(ttl=3600)
def fetch_and_parse_ts():
    all_alternatives = []
    
    for file_name in FILES:
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/src/data/{file_name}"
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                continue
                
            content = resp.text
            
            # ZURÜCK ZUM 111-DIENSTE-SPLITTER: 
            # Teilt nur sauber an echten Objekt-Anfängen (Zeilenanfang + name:)
            blocks = re.split(r'(?m)^\s*(?:["\']?name["\']?)\s*:\s*', content)
            
            for block in blocks[1:]:
                # 1. Name
                name_match = re.search(r'^([\'"`])(.*?)\1', block)
                if not name_match: continue
                name = name_match.group(2).strip()
                
                # 2. Replaces (Bulletproof für Listen UND einzelne Strings)
                replaces_str = ""
                rep_match = re.search(r'["\']?replaces["\']?\s*:\s*(\[.*?\]|[\'"`].*?[\'"`])', block, re.DOTALL)
                if rep_match:
                    raw_replaces = rep_match.group(1)
                    # Alle Begriffe in Anführungszeichen rausziehen
                    items = re.findall(r'[\'"`](.*?)[\'"`]', raw_replaces)
                    if items:
                        replaces_str = ", ".join(items)
                    else:
                        # Fallback für Listen ohne Anführungszeichen
                        replaces_str = re.sub(r'[\[\]]', '', raw_replaces).strip()
                
                # 3. Description (Mehrzeilen-Modus)
                desc_str = ""
                desc_match = re.search(r'["\']?(?:description|desc|notes|info)["\']?\s*:\s*([\'"`])([\s\S]*?)\1', block, re.IGNORECASE)
                if desc_match:
                    desc_str = re.sub(r'\s+', ' ', desc_match.group(2)).strip()
                
                # 4. URL
                url_str = ""
                url_match = re.search(r'["\']?(?:url|website|link)["\']?\s*:\s*([\'"`])(.*?)\1', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(2).strip()
                
                all_alternatives.append({
                    "name": name,
                    "replaces": replaces_str,
                    "description": desc_str,
                    "url": url_str
                })
        except Exception:
            continue
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Durchsuche europäische Alternativen zu US-Software.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach Dienst (z.B. OneDrive, Outlook, Cloud, WhatsApp):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        # ULTIMATIVE SUCHE: Durchsucht Name, Replaces UND Beschreibung
        results = [d for d in data if 
                   q in d["name"].lower() or 
                   q in d["replaces"].lower() or 
                   q in d["description"].lower()]
        
        if results:
            st.success(f"{len(results)} Treffer gefunden:")
            for r in results:
                with st.container():
                    st.markdown(f"### {r['name']}")
                    if r['replaces']:
                        st.write(f"**Ersetzt:** {r['replaces']}")
                    if r['description']:
                        st.write(f"**Details:** {r['description']}")
                    
                    if r['url']:
                        st.link_button("🌐 Zur Webseite", r['url'])
                    st.divider()
        else:
            st.info(f"Kein Treffer für '{query}'.")

with st.sidebar:
    st.header("Info")
    st.write(f"Dienste in der Datenbank: **{len(data)}**")
    st.markdown("[Hauptprojekt (GitHub)](https://github.com/TheMorpheus407/european-alternatives)")
    st.markdown("[App-Quellcode](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
