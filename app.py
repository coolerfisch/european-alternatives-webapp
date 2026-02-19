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
            
            # Die robusteste Methode: Wir splitten an JEDER geschweiften Klammer {
            # Damit haben wir jeden Dienst sicher isoliert, egal wie er formatiert ist.
            blocks = content.split('{')
            
            for block in blocks:
                # 1. Name
                name_match = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', block)
                if not name_match:
                    continue # Wenn kein Name drin ist, ist es kein Dienst
                name = name_match.group(1).strip()
                
                # 2. Replaces (Sucht in Arrays ODER in einfachen Strings)
                replaces_str = ""
                rep_match = re.search(r'replaces\s*:\s*\[([\s\S]*?)\]', block)
                if rep_match:
                    items = re.findall(r'[\'"`](.*?)[\'"`]', rep_match.group(1))
                    replaces_str = ", ".join(items)
                else:
                    rep_single = re.search(r'replaces\s*:\s*[\'"`](.*?)[\'"`]', block)
                    if rep_single:
                        replaces_str = rep_single.group(1)
                
                # 3. URL
                url_str = ""
                url_match = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(1).strip()
                
                # Ohne Beschreibung!
                all_alternatives.append({
                    "name": name,
                    "replaces": replaces_str,
                    "url": url_str
                })
        except Exception:
            continue
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Finde europäische Alternativen zu US-Software.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        # Suche jetzt nur noch in Name und Replaces
        results = [d for d in data if 
                   q in d["name"].lower() or 
                   q in d["replaces"].lower()]
        
        if results:
            st.success(f"{len(results)} Treffer gefunden:")
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
    st.header("Info")
    st.write(f"Indexierte Dienste: **{len(data)}**")
    st.markdown("[Hauptprojekt (GitHub)](https://github.com/TheMorpheus407/european-alternatives)")
    st.markdown("[App-Quellcode](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
