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
            
            # Wir splitten den Text exakt am Schlüsselwort "name:"
            # Das Wort "\bname" stellt sicher, dass es ein eigenständiges Wort ist.
            blocks = re.split(r'\bname\s*:\s*', content)
            
            for block in blocks[1:]:
                # 1. Name: Da wir bei "name:" gesplittet haben, steht der Name direkt am Anfang
                name_match = re.search(r'^([\'"`])(.*?)\1', block)
                if not name_match:
                    continue
                name = name_match.group(2).strip()
                
                # 2. Replaces: Zieht Arrays [...] oder einzelne Strings "..." heraus (auch über mehrere Zeilen)
                replaces_str = ""
                rep_match = re.search(r'\breplaces\s*:\s*(\[[\s\S]*?\]|[\'"`][\s\S]*?[\'"`])', block)
                if rep_match:
                    raw_rep = rep_match.group(1)
                    # Alle Begriffe in Anführungszeichen aus dem Treffer filtern
                    items = re.findall(r'[\'"`](.*?)[\'"`]', raw_rep)
                    replaces_str = ", ".join(items)
                
                # 3. URL
                url_str = ""
                url_match = re.search(r'\b(?:url|website|link)\s*:\s*([\'"`])(.*?)\1', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(2).strip()
                
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
