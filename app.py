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
                
            lines = resp.text.split('\n')
            current_item = {}
            in_replaces_array = False
            
            for line in lines:
                # 1. Name: Startet ein neues Objekt
                name_match = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', line)
                if name_match:
                    if 'name' in current_item:
                        # Vorheriges Element abschließen und speichern
                        current_item['replaces'] = ", ".join(current_item.get('replaces_list', []))
                        all_alternatives.append(current_item)
                    
                    # Neues Element initialisieren
                    current_item = {
                        'name': name_match.group(1),
                        'replaces_list': [],
                        'url': ''
                    }
                    in_replaces_array = False
                    continue
                
                # 2. Replaces: Start der Liste oder Einzeiler
                if 'replaces' in line and not in_replaces_array:
                    # Finde den Doppelpunkt und nimm alle Strings in Anführungszeichen danach
                    colon_idx = line.find(':')
                    if colon_idx != -1:
                        items = re.findall(r'[\'"`](.*?)[\'"`]', line[colon_idx:])
                        current_item.setdefault('replaces_list', []).extend(items)
                    
                    # Prüfen, ob ein Array geöffnet, aber nicht geschlossen wird
                    if '[' in line and ']' not in line:
                        in_replaces_array = True
                    continue
                
                # 3. Replaces: Mehrzeilige Arrays abarbeiten
                if in_replaces_array:
                    items = re.findall(r'[\'"`](.*?)[\'"`]', line)
                    current_item.setdefault('replaces_list', []).extend(items)
                    if ']' in line:
                        in_replaces_array = False
                    continue
                
                # 4. URL
                url_match = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', line, re.IGNORECASE)
                if url_match:
                    current_item['url'] = url_match.group(1)

            # Letztes Element der Datei speichern
            if 'name' in current_item:
                current_item['replaces'] = ", ".join(current_item.get('replaces_list', []))
                all_alternatives.append(current_item)

        except Exception as e:
            st.error(f"Fehler beim Parsen von {file_name}: {e}")
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Finde europäische Alternativen zu US-Software.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        # Suche durchsucht Name und Replaces
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
