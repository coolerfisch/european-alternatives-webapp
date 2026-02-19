import streamlit as st
import requests
import re

# --- Konfiguration ---
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
            
            text = resp.text
            
            # Wir suchen alle "name:" als Ankerpunkte
            pattern_name = re.compile(r'\bname\s*:\s*([\'"`])(.*?)\1')
            matches = list(pattern_name.finditer(text))
            
            for i in range(len(matches)):
                start_idx = matches[i].start()
                end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
                block = text[start_idx:end_idx]
                
                name = matches[i].group(2).strip()
                
                # --- JETZT MIT DEN KORREKTEN KEYS ---
                
                # 1. replacesUS (Das war der Fehler!)
                replaces_list = []
                # Sucht nach replacesUS: [...] oder replacesUS: "..."
                rep_match = re.search(r'replacesUS\s*:\s*(\[[\s\S]*?\]|[\'"`][\s\S]*?[\'"`])', block)
                if rep_match:
                    raw_rep = rep_match.group(1)
                    replaces_list = re.findall(r'[\'"`](.*?)[\'"`]', raw_rep)
                
                # 2. URL / Website
                url_str = ""
                # Im Code oben sehe ich 'website', wir prüfen zur Sicherheit alles
                url_match = re.search(r'\b(?:url|website|link)\s*:\s*([\'"`])(.*?)\1', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(2).strip()
                
                all_alternatives.append({
                    "name": name,
                    "replaces": ", ".join(replaces_list),
                    "url": url_str
                })
        except Exception as e:
            st.error(f"Fehler in {file_name}: {e}")
            
    return all_alternatives

# --- User Interface ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Suche nach europäischen Alternativen zu US-Software (OneDrive, Outlook, etc.)")

data = fetch_and_parse_ts()

if data:
    # Suchfeld
    query = st.text_input("Welchen US-Dienst möchtest du ersetzen?", placeholder="z.B. OneDrive oder Outlook...")

    if query:
        q = query.lower().strip()
        # Suche in Name und in der (jetzt korrekten) Replaces-Liste
        results = [d for d in data if q in d["name"].lower() or q in d["replaces"].lower()]
        
        if results:
            st.success(f"{len(results)} Treffer für '{query}' gefunden:")
            for r in results:
                with st.container():
                    st.markdown(f"### {r['name']}")
                    if r['replaces']:
                        st.write(f"**Ersetzt:** {r['replaces']}")
                    
                    if r['url']:
                        st.link_button("🌐 Zur Webseite", r['url'])
                    st.divider()
        else:
            st.info(f"Kein direkter Treffer für '{query}'. Versuche es mit einem allgemeineren Begriff.")

with st.sidebar:
    st.header("Statistik")
    st.write(f"Indexierte Dienste: **{len(data)}**")
    st.write("---")
    st.markdown("**Quellcode der App:**")
    st.markdown("[GitHub: european-alternatives-webapp](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
