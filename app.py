import streamlit as st
import requests
import re

# Konfiguration
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

def extract_ts_objects(text):
    """
    Compiler-ähnlicher Tokenizer: Zählt geschweifte Klammern, um verschachtelte 
    TypeScript-Objekte sicher und isoliert zu extrahieren.
    """
    objects = []
    brace_level = 0
    in_string = False
    string_char = ''
    current_obj = []
    
    # Finde den Start des Haupt-Arrays
    start_idx = text.find('[')
    if start_idx == -1: return []
    
    skip_next = False
    
    for char in text[start_idx:]:
        if skip_next:
            if brace_level > 0: current_obj.append(char)
            skip_next = False
            continue
            
        if char == '\\':
            if brace_level > 0: current_obj.append(char)
            skip_next = True
            continue

        if char in ("'", '"', '`'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
            if brace_level > 0: current_obj.append(char)
            continue

        if not in_string:
            if char == '{':
                brace_level += 1
            
            if brace_level > 0:
                current_obj.append(char)
                
            if char == '}':
                brace_level -= 1
                if brace_level == 0 and current_obj:
                    # Ein vollständiges, isoliertes Objekt wurde gefunden
                    objects.append("".join(current_obj))
                    current_obj = []
                    
    return objects

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
            
            # Zerlege den Code in saubere Blöcke mittels Tokenizer
            blocks = extract_ts_objects(text)
            
            for block in blocks:
                # 1. Name: Sucht nun sicher im isolierten Block
                name_match = re.search(r'\bname\s*:\s*[\'"`](.*?)[\'"`]', block)
                if not name_match:
                    continue
                name = name_match.group(1).strip()
                
                # 2. Replaces: Greift Arrays oder Einzelstrings
                replaces_str = ""
                rep_match = re.search(r'\breplaces\s*:\s*(\[[\s\S]*?\]|[\'"`][\s\S]*?[\'"`])', block)
                if rep_match:
                    raw_rep = rep_match.group(1)
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
        except Exception as e:
            st.error(f"Systemfehler in {file_name}: {e}")
            
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
