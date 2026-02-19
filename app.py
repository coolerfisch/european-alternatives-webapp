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
    debug_logs = []
    
    for file_name in FILES:
        # Check both main and master branches
        urls_to_try = [
            f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/src/data/{file_name}",
            f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/master/src/data/{file_name}"
        ]
        
        content = None
        used_url = None
        for url in urls_to_try:
            resp = requests.get(url)
            if resp.status_code == 200:
                content = resp.text
                used_url = url
                break
        
        if not content:
            debug_logs.append(f"❌ {file_name}: 404 Not Found (Weder in main noch in master)")
            continue
            
        debug_logs.append(f"✅ {file_name}: Erfolgreich geladen aus dem {used_url.split('/')[5]} branch")
        
        # Parsen des Inhalts durch Splitten an der geschweiften Klammer
        blocks = content.split('{')
        for block in blocks:
            # Suche nach Name (akzeptiert einfache und doppelte Anfuehrungszeichen)
            name_match = re.search(r'["\']?name["\']?\s*:\s*[\'"`](.*?)[\'"`]', block)
            if not name_match:
                continue
                
            name = name_match.group(1)
            
            # Suche nach replaces (Array oder einzelner String)
            replaces_str = ""
            replaces_match = re.search(r'["\']?replaces["\']?\s*:\s*\[(.*?)\]', block, re.DOTALL)
            if replaces_match:
                items = re.findall(r'[\'"`](.*?)[\'"`]', replaces_match.group(1))
                replaces_str = ", ".join(items)
            else:
                rep_single = re.search(r'["\']?replaces["\']?\s*:\s*[\'"`](.*?)[\'"`]', block)
                if rep_single:
                    replaces_str = rep_single.group(1)
                    
            # Suche nach description
            desc_str = "Keine Beschreibung verfuegbar."
            desc_match = re.search(r'["\']?description["\']?\s*:\s*[\'"`](.*?)[\'"`]', block, re.DOTALL)
            if desc_match:
                # Bereinigt eventuelle Zeilenumbrueche innerhalb der Beschreibung
                desc_str = desc_match.group(1).replace('\n', ' ').strip()
                
            # Suche nach url
            url_str = ""
            url_match = re.search(r'["\']?url["\']?\s*:\s*[\'"`](.*?)[\'"`]', block)
            if url_match:
                url_str = url_match.group(1)
                
            all_alternatives.append({
                "name": name,
                "replaces": replaces_str,
                "description": desc_str,
                "url": url_str
            })
            
    return all_alternatives, debug_logs

# --- User Interface ---
st.title("Digitaler Souveraenitaets-Check")
st.write("Live-Anbindung an die Kataloge des European Alternatives Projekts.")

data, logs = fetch_and_parse_ts()

# Diagnose-Panel (oeffnet sich automatisch, wenn ein Fehler vorliegt)
with st.expander("System-Diagnose", expanded=not bool(data)):
    for log in logs:
        st.write(log)
    if not data:
        st.error("Kritischer Fehler: Keine validen Datenstrukturen gefunden.")

if not data:
    st.warning("Verbindung fehlerhaft oder Datenstruktur leer. Bitte System-Diagnose pruefen.")
else:
    query = st.text_input("Suche nach US-Dienst (z.B. WhatsApp, Gmail, Dropbox):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        results = [d for d in data if q in d.get("replaces", "").lower() or q in d.get("name", "").lower()]
        
        if results:
            st.success(f"{len(results)} Alternative(n) gefunden:")
            for r in results:
                with st.container():
                    st.markdown(f"### {r['name']}")
                    st.write(f"**Ersetzt:** {r['replaces']}")
                    st.write(f"**Details:** {r['description']}")
                    
                    if r.get('url'):
                        st.link_button("Zur Webseite", r['url'])
                        
                    st.divider()
        else:
            st.info(f"Kein Treffer fuer '{query}'. Versuche es mit allgemeineren Begriffen.")

with st.sidebar:
    st.header("Über das Tool")
    st.write(f"Aktuell indexierte Dienste: **{len(data)}**")
    st.markdown("Dieses Tool parst den Quellcode des [European Alternatives](https://github.com/TheMorpheus407/european-alternatives) Projekts.")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
