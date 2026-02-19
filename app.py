import streamlit as st
import requests
import re

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

@st.cache_data(ttl=3600)
def fetch_raw_data():
    all_alternatives = []
    # Wir nehmen genau die Dateien aus dem von dir verlinkten Ordner
    files = ["manualAlternatives.ts", "researchAlternatives.ts"]
    
    for file_name in files:
        url = f"https://raw.githubusercontent.com/TheMorpheus407/european-alternatives/main/src/data/{file_name}"
        try:
            resp = requests.get(url)
            if resp.status_code != 200: continue
            
            # Wir suchen einfach nach ALLEM, was zwischen { und } steht
            # und einen "name" Eintrag hat.
            raw_content = resp.text
            # Trenne bei jedem Objekt-Anfang
            potential_blocks = raw_content.split('{')
            
            for block in potential_blocks:
                if 'name:' in block or '"name":' in block:
                    # Extrahiere Name
                    n = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', block)
                    # Extrahiere URL
                    u = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', block, re.IGNORECASE)
                    # Extrahiere Replaces (findet alles in Anführungszeichen nach dem Wort replaces)
                    r_block = re.search(r'replaces\s*:\s*\[?([\s\S]*?)\]?[,\n]', block)
                    replaces = ""
                    if r_block:
                        found_reps = re.findall(r'[\'"`](.*?)[\'"`]', r_block.group(1))
                        replaces = ", ".join(found_reps)
                    
                    if n:
                        all_alternatives.append({
                            "name": n.group(1),
                            "replaces": replaces,
                            "url": u.group(1) if u else ""
                        })
        except:
            continue
    return all_alternatives

st.title("🇪🇺 European Alternatives Web-App")
data = fetch_raw_data()

query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Outlook, Google):")

if query:
    q = query.lower()
    results = [d for d in data if q in d['name'].lower() or q in d['replaces'].lower()]
    
    if results:
        for res in results:
            with st.expander(f"⭐ {res['name']}", expanded=True):
                st.write(f"**Alternative für:** {res['replaces']}")
                if res['url']:
                    st.link_button("Zur Webseite", res['url'])
    else:
        st.info("Keine Treffer gefunden.")

st.sidebar.write(f"Indexierte Dienste: {len(data)}")
