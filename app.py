import streamlit as st
import requests
import re

# Konfiguration
REPO_BASE = "https://raw.githubusercontent.com/TheMorpheus407/european-alternatives/main/src/data/"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

@st.cache_data(ttl=3600)
def fetch_and_parse_ts():
    all_alternatives = []
    
    for file_name in FILES:
        url = REPO_BASE + file_name
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                continue
                
            lines = resp.text.split('\n')
            current_item = {}
            in_replaces_array = False
            
            for line in lines:
                line = line.strip()
                
                # 1. Suche nach dem Namen
                name_match = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', line)
                if name_match:
                    if 'name' in current_item:
                        if 'replaces_list' in current_item:
                            current_item['replaces'] = ", ".join(current_item['replaces_list'])
                        else:
                            current_item['replaces'] = ""
                        all_alternatives.append(current_item)
                        current_item = {}
                    
                    current_item['name'] = name_match.group(1)
                    current_item['replaces_list'] = []
                    current_item['description'] = "Keine Beschreibung verfuegbar."
                    current_item['url'] = ""
                    continue
                
                # 2. Suche nach der "replaces" Liste
                if 'replaces' in line and '[' in line:
                    inline_items = re.findall(r'[\'"`](.*?)[\'"`]', line[line.find('['):])
                    if inline_items:
                        current_item.setdefault('replaces_list', []).extend(inline_items)
                    
                    if ']' not in line:
                        in_replaces_array = True
                    continue
                
                # 3. Mehrzeilige Listen
                if in_replaces_array:
                    array_items = re.findall(r'[\'"`](.*?)[\'"`]', line)
                    if array_items:
                        current_item.setdefault('replaces_list', []).extend(array_items)
                    if ']' in line:
                        in_replaces_array = False
                    continue
                
                # 4. Suche nach der Beschreibung
                desc_match = re.search(r'description\s*:\s*[\'"`](.*?)[\'"`]', line)
                if desc_match:
                    current_item['description'] = desc_match.group(1)

                # 5. NEU: Suche nach der URL
                url_match = re.search(r'url\s*:\s*[\'"`](.*?)[\'"`]', line)
                if url_match:
                    current_item['url'] = url_match.group(1)

            # Letztes Item hinzufuegen
            if 'name' in current_item:
                if 'replaces_list' in current_item:
                    current_item['replaces'] = ", ".join(current_item['replaces_list'])
                else:
                    current_item['replaces'] = ""
                all_alternatives.append(current_item)

        except Exception as e:
            st.error(f"Fehler beim Parsen von {file_name}: {e}")
            
    return all_alternatives

# --- User Interface ---
st.title("Digitaler Souveraenitaets-Check")
st.write("Live-Anbindung an die Kataloge des European Alternatives Projekts.")

data = fetch_and_parse_ts()

if not data:
    st.warning("Verbindung zu GitHub wird aufgebaut oder Datenstruktur ist leer...")
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
                    
                    # NEU: Der klickbare Button, falls eine URL gefunden wurde
                    if r.get('url'):
                        st.link_button("Zur Webseite", r['url'])
                        
                    st.divider()
        else:
            st.info(f"Kein Treffer fuer '{query}'. Versuche es mit allgemeineren Begriffen.")

with st.sidebar:
    st.header("Über das Tool")
    st.write(f"Aktuell indexierte Dienste: **{len(data)}**")
    
    # NEU: Korrekte Markdown-Syntax fuer funktionierende Links
    st.markdown("Dieses Tool parst direkt den TypeScript-Quellcode des [European Alternatives](https://github.com/TheMorpheus407/european-alternatives) Projekts.")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
