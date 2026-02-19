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
        # Wir prüfen nacheinander main und master Branch
        content = ""
        for branch in ["main", "master"]:
            url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{branch}/src/data/{file_name}"
            resp = requests.get(url)
            if resp.status_code == 200:
                content = resp.text
                break
        
        if not content:
            continue
            
        # BRUTE FORCE: Wir suchen alle Blöcke zwischen { und } 
        # die mindestens ein "name:" enthalten.
        blocks = re.findall(r'\{[\s\S]*?name\s*:\s*[\'"`].*?[\'"`][\s\S]*?\}', content)
        
        for block in blocks:
            # 1. Name extrahieren
            name_match = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', block)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # 2. Replaces extrahieren
            # Wir nehmen ALLES, was in Anführungszeichen steht, nachdem "replaces" auftaucht
            replaces_list = []
            replaces_part = re.search(r'replaces\s*:\s*\[([\s\S]*?)\]', block)
            if replaces_part:
                # Mehrere Dienste in einer Liste
                replaces_list = re.findall(r'[\'"`](.*?)[\'"`]', replaces_part.group(1))
            else:
                # Ein einzelner Dienst ohne Liste
                single_rep = re.search(r'replaces\s*:\s*[\'"`](.*?)[\'"`]', block)
                if single_rep:
                    replaces_list = [single_rep.group(1)]
            
            # 3. URL extrahieren
            url_match = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', block, re.IGNORECASE)
            url_val = url_match.group(1).strip() if url_match else ""
            
            all_alternatives.append({
                "name": name,
                "replaces": ", ".join(replaces_list),
                "url": url_val
            })
            
    return all_alternatives

# --- User Interface ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Direkt-Abfrage der europäischen Alternativen.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort...")

    if query:
        q = query.lower().strip()
        results = [d for d in data if q in d["name"].lower() or q in d["replaces"].lower()]
        
        if results:
            st.success(f"{len(results)} Treffer gefunden.")
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
    st.write(f"Gefundene Dienste: **{len(data)}**")
    st.write("---")
    st.markdown("[App-Quellcode](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("Mitwirkender: coolerfisch")
