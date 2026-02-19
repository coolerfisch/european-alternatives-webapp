import streamlit as st
import requests
import re

# --- Konfiguration ---
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

def extract_top_level_objects(text: str) -> list[str]:
    """
    Sucht das äußere Array [...] und extrahiert nur die darin liegenden
    Top-Level-Objekte { ... }. Ignoriert verschachtelte Sub-Objekte.
    """
    # Erst das äußere Array [...] finden (hinter dem Gleichheitszeichen)
    array_match = re.search(r'=\s*\[', text)
    if not array_match:
        return []
    
    start_pos = array_match.end() - 1  # Position des '['
    text_segment = text[start_pos:]
    
    objects = []
    depth = 0        # Trackt eckige Klammern [ ]
    brace_depth = 0  # Trackt geschweifte Klammern { }
    start = -1
    in_string = False
    string_char = None
    i = 0

    while i < len(text_segment):
        char = text_segment[i]

        # String-Handling (Escapes ignorieren)
        if not in_string and char in ('"', "'", '`'):
            in_string = True
            string_char = char
        elif in_string:
            if char == '\\':
                i += 2
                continue
            if char == string_char:
                in_string = False

        # Klammern nur außerhalb von Strings zählen
        if not in_string:
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0: break # Ende des Haupt-Arrays erreicht
            
            elif char == '{':
                # Ein neues Objekt beginnt nur, wenn wir direkt im Haupt-Array sind (depth == 1)
                if brace_depth == 0 and depth == 1:
                    start = i
                brace_depth += 1
            
            elif char == '}':
                brace_depth -= 1
                # Ein Objekt ist fertig, wenn wir zurück auf die erste Klammer-Ebene fallen
                if brace_depth == 0 and start != -1:
                    objects.append(text_segment[start:i+1])
                    start = -1
        i += 1

    return objects

def parse_value(raw: str) -> str:
    raw = raw.strip().rstrip(',')
    if raw.startswith('['):
        items = re.findall(r'[\'"`]([^\'"`]+)[\'"`]', raw)
        return ', '.join(items)
    m = re.match(r'^[\'"`]([\s\S]*?)[\'"`]$', raw)
    if m:
        return m.group(1).strip()
    return ""

def parse_field(block: str, keys: list[str]) -> str:
    for key in keys:
        # Sucht den Key am Zeilenanfang innerhalb des isolierten Blocks
        pattern = rf'^\s*{key}\s*:\s*(.+?)(?=,?\s*\n\s*\w+\s*:|,?\s*\n?\s*\}})'
        m = re.search(pattern, block, re.MULTILINE | re.DOTALL)
        if m:
            return parse_value(m.group(1))
    return ""

@st.cache_data(ttl=3600)
def fetch_and_parse_ts():
    all_alternatives = []
    
    for file_name in FILES:
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/src/data/{file_name}"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                text = resp.text
                blocks = extract_top_level_objects(text)
                
                # --- Diagnose-Ausgabe (kann später entfernt werden) ---
                # st.sidebar.write(f"DEBUG: {file_name} -> {len(blocks)} Blöcke")
                
                for block in blocks:
                    name = parse_field(block, ['name'])
                    if not name: continue
                    
                    replaces = parse_field(block, ['replaces'])
                    url_str = parse_field(block, ['url', 'website', 'link'])
                    
                    all_alternatives.append({
                        "name": name,
                        "replaces": replaces,
                        "url": url_str
                    })
        except Exception as e:
            st.error(f"Fehler in {file_name}: {e}")
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Präzises Parsing der European Alternatives Daten.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche nach US-Dienst (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort eingeben...")

    if query:
        q = query.lower().strip()
        results = [d for d in data if q in d["name"].lower() or q in d["replaces"].lower()]
        
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
    st.header("Statistik")
    st.write(f"Indexierte Dienste: **{len(data)}**")
    st.write("---")
    st.markdown("[GitHub Repository](https://github.com/TheMorpheus407/european-alternatives)")
    st.write("Mitwirkender: coolerfisch")
