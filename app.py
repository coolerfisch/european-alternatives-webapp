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
            in_description = False
            desc_quote_char = ""
            
            for line in lines:
                line = line.strip()
                
                # 1. Name
                name_match = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', line)
                if name_match:
                    if 'name' in current_item:
                        current_item['replaces'] = ", ".join(current_item.get('replaces_list', []))
                        all_alternatives.append(current_item)
                        current_item = {}
                    
                    current_item['name'] = name_match.group(1)
                    current_item['replaces_list'] = []
                    current_item['description'] = "Keine Beschreibung verfügbar."
                    current_item['description_lines'] = []
                    current_item['url'] = ""
                    in_replaces_array = False
                    in_description = False
                    continue

                # 2. Mehrzeilige Beschreibung fortführen
                if in_description:
                    if desc_quote_char in line:
                        # Ende der Beschreibung gefunden (schließendes Anführungszeichen/Backtick)
                        current_item['description_lines'].append(line.split(desc_quote_char)[0])
                        current_item['description'] = " ".join(current_item['description_lines']).strip()
                        in_description = False
                    else:
                        current_item['description_lines'].append(line)
                    continue
                
                # 3. Replaces Liste
                if 'replaces' in line and '[' in line:
                    inline_items = re.findall(r'[\'"`](.*?)[\'"`]', line[line.find('['):])
                    if inline_items:
                        current_item.setdefault('replaces_list', []).extend(inline_items)
                    if ']' not in line:
                        in_replaces_array = True
                    continue
                
                if in_replaces_array:
                    array_items = re.findall(r'[\'"`](.*?)[\'"`]', line)
                    if array_items:
                        current_item.setdefault('replaces_list', []).extend(array_items)
                    if ']' in line:
                        in_replaces_array = False
                    continue
                
                # 4. Description Start
                desc_match = re.search(r'description\s*:\s*(["\'`])(.*)', line)
                if desc_match:
                    quote_char = desc_match.group(1)
                    rest_of_line = desc_match.group(2)
                    
                    if quote_char in rest_of_line:
                        # Einzeilige Beschreibung (öffnet und schließt in derselben Zeile)
                        current_item['description'] = rest_of_line.split(quote_char)[0]
                    else:
                        # Start einer mehrzeiligen Beschreibung
                        in_description = True
                        desc_quote_char = quote_char
                        current_item['description_lines'] = [rest_of_line]
                    continue

                # 5. URL / Website / Link
                url_match = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', line, re.IGNORECASE)
                if url_match:
                    current_item['url'] = url_match.group(1)

            # Letztes Element der Datei abspeichern
            if 'name' in current_item:
                current_item['replaces'] = ", ".join(current_item.get('replaces_list', []))
                all_alternatives.append(current_item)

        except Exception as e:
            st.error(f"Fehler beim Parsen von {file_name}: {e}")
            
    return all_alternatives

# --- User Interface ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
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
                    
                    # Button-Ausgabe
                    if r.get('url'):
                        # Kleiner Trick mit Streamlit Columns, damit der Button nicht die ganze Breite einnimmt
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            st.link_button("🌐 Zur Webseite", r['url'])
                        
                    st.divider()
        else:
            st.info(f"Kein Treffer für '{query}'. Versuche es mit allgemeineren Begriffen.")

with st.sidebar:
    st.header("Über das Tool")
    st.write(f"Aktuell indexierte Dienste: **{len(data)}**")
    st.markdown("Dieses Tool parst den Quellcode des [European Alternatives](https://github.com/TheMorpheus407/european-alternatives) Projekts.")
    st.write("---")
    st.markdown("**Quellcode dieser App:**")
    st.markdown("[GitHub: coolerfisch/european-alternatives-webapp](https://github.com/coolerfisch/european-alternatives-webapp/)")
    st.write("---")
    st.write("Mitwirkender: coolerfisch")
