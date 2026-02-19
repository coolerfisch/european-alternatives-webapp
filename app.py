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
            # Teile den Text an jedem "name:"
            blocks = re.split(r'(?m)^\s*(?:["\']?name["\']?)\s*:\s*', content)
            
            for block in blocks[1:]:
                # 1. Name
                name_match = re.search(r'^([\'"`])(.*?)\1', block)
                if not name_match: continue
                name = name_match.group(2).strip()
                
                # 2. Replaces (Extrem flexibel: Array [] oder einzelner String)
                replaces_str = ""
                # Suche nach [ ... ]
                rep_array_match = re.search(r'replaces\s*:\s*\[([\s\S]*?)\]', block)
                if rep_array_match:
                    items = re.findall(r'[\'"`](.*?)[\'"`]', rep_array_match.group(1))
                    replaces_str = ", ".join(items)
                else:
                    # Suche nach einfachem String "..."
                    rep_single_match = re.search(r'replaces\s*:\s*[\'"`](.*?)[\'"`]', block)
                    if rep_single_match:
                        replaces_str = rep_single_match.group(1)
                
                # 3. Beschreibung (Dotall für Mehrzeiler)
                desc_str = ""
                desc_match = re.search(r'(?:description|desc|notes|info)\s*:\s*([\'"`])(.*?)\1', block, re.DOTALL | re.IGNORECASE)
                if desc_match:
                    desc_str = re.sub(r'\s+', ' ', desc_match.group(2)).strip()
                
                # 4. URL
                url_str = ""
                url_match = re.search(r'(?:url|website|link)\s*:\s*([\'"`])(.*?)\1', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(2).strip()
                
                all_alternatives.append({
                    "name": name,
                    "replaces": replaces_str,
                    "description": desc_str,
                    "url": url_str
                })
        except Exception as e:
            st.error(f"Fehler: {e}")
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Live-Suche in den Daten von European Alternatives.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach Dienst (z.B. OneDrive, Outlook, WhatsApp, Cloud):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        # ERWEITERTE SUCHE: Prüft jetzt Name, Replaces UND Beschreibung
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
    st.write(f"Indexierte Dienste: **{len(data)}**")
    st.markdown("[Hauptprojekt (GitHub)](https://github.com/TheMorpheus407/european-alternatives)")
    st.markdown("[App-Quellcode](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
