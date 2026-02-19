import streamlit as st
import requests
import re

# --- Konfiguration ---
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

# --- Claudes Parser-Logik ---
def extract_top_level_objects(text: str) -> list[str]:
    """
    Extrahiert alle Top-Level-Objekte { ... } aus dem TS-Array.
    Robust gegen Verschachtelung, ignoriert Klammern in Strings.
    """
    objects = []
    depth = 0
    start = -1
    in_string = False
    string_char = None
    i = 0

    while i < len(text):
        char = text[i]

        # String-Erkennung (einfach, doppelt, Backtick)
        if not in_string and char in ('"', "'", '`'):
            in_string = True
            string_char = char
        elif in_string:
            if char == '\\':
                i += 2  # Escape-Sequenz überspringen
                continue
            if char == string_char:
                in_string = False

        # Klammern nur außerhalb von Strings zählen
        if not in_string:
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    objects.append(text[start:i+1])
                    start = -1
        i += 1

    return objects

def parse_value(raw: str) -> str:
    """
    Extrahiert den Wert aus einem rohen TS-Ausdruck.
    Unterstützt Arrays und Strings. Ignoriert TS-Funktionen.
    """
    raw = raw.strip().rstrip(',')

    # Array: ['a', 'b', "c"]
    if raw.startswith('['):
        items = re.findall(r'[\'"`]([^\'"`]+)[\'"`]', raw)
        return ', '.join(items)

    # Einfacher String
    m = re.match(r'^[\'"`]([\s\S]*?)[\'"`]$', raw)
    if m:
        return m.group(1).strip()

    return ""

def parse_field(block: str, keys: list[str]) -> str:
    """
    Sucht nach einem der angegebenen Keys im Block und gibt den Wert zurück.
    """
    for key in keys:
        # Key am Zeilenanfang, gefolgt von ':'
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
                blocks = extract_top_level_objects(resp.text)
                
                for block in blocks:
                    name = parse_field(block, ['name'])
                    if not name:
                        continue  # Kein Name -> kein gültiger Eintrag
                    
                    replaces = parse_field(block, ['replaces'])
                    url_str = parse_field(block, ['url', 'website', 'link'])
                    
                    all_alternatives.append({
                        "name": name,
                        "replaces": replaces,
                        "url": url_str
                    })
        except Exception as e:
            st.error(f"Fehler beim Parsen von {file_name}: {e}")
            
    return all_alternatives

# --- User Interface ---
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
