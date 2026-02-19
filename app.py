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
            
            # Wir suchen einfach alle Namen im gesamten Text
            # Pattern: findet 'name: "Wert"'
            name_matches = list(re.finditer(r'name\s*:\s*[\'"`](.*?)[\'"`]', content))
            
            for i in range(len(name_matches)):
                start_pos = name_matches[i].start()
                # Der Bereich für diesen Dienst geht bis zum Start des nächsten Namens
                end_pos = name_matches[i+1].start() if i+1 < len(name_matches) else len(content)
                block = content[start_pos:end_pos]
                
                name = name_matches[i].group(1).strip()
                
                # Replaces im Block suchen
                replaces_str = ""
                # Sucht nach replaces: ["a", "b"] ODER replaces: "a"
                rep_match = re.search(r'replaces\s*:\s*(\[.*?\]|[\'"`].*?[\'"`])', block, re.DOTALL)
                if rep_match:
                    found = rep_match.group(1)
                    # Alle Begriffe in Anführungszeichen extrahieren
                    items = re.findall(r'[\'"`](.*?)[\'"`]', found)
                    replaces_str = ", ".join(items)
                
                # URL im Block suchen
                url_str = ""
                url_match = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(1).strip()
                
                all_alternatives.append({
                    "name": name,
                    "replaces": replaces_str,
                    "url": url_str
                })
        except:
            continue
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Live-Daten aus dem European Alternatives Katalog.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        # Suche in Name und Replaces
        results = [d for d in data if q in d["name"].lower() or q in d["replaces"].lower()]
        
        if results:
            st.success(f"{len(results)} Alternative(n) gefunden:")
            for r in results:
                with st.container():
                    st.markdown(f"### {r['name']}")
                    if r['replaces']:
                        st.write(f"**Ersetzt:** {r['replaces']}")
                    if r['url']:
                        st.link_button("🌐 Zur Webseite", r['url'])
                    st.divider()
        else:
            st.info(f"Kein Treffer für '{query}'.")

with st.sidebar:
    st.header("Statistik")
    st.write(f"Indexierte Dienste: **{len(data)}**")
    st.markdown("[Quellcode dieser App](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
