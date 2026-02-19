import streamlit as st
import requests
import re

# --- Konfiguration ---
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
FILES = ["manualAlternatives.ts", "researchAlternatives.ts"]

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

def extract_top_level_objects(text: str) -> list[str]:
    # Sucht das Haupt-Array hinter dem Gleichheitszeichen
    array_match = re.search(r'=\s*\[', text)
    if not array_match: return []
    
    start_pos = array_match.end() - 1
    text_segment = text[start_pos:]
    
    objects = []
    depth = 0
    brace_depth = 0
    start = -1
    in_string = False
    string_char = None
    i = 0

    while i < len(text_segment):
        char = text_segment[i]
        if not in_string and char in ('"', "'", '`'):
            in_string = True
            string_char = char
        elif in_string:
            if char == '\\':
                i += 2
                continue
            if char == string_char:
                in_string = False
        
        if not in_string:
            if char == '[': depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0: break
            elif char == '{':
                if brace_depth == 0 and depth == 1: start = i
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0 and start != -1:
                    objects.append(text_segment[start:i+1])
                    start = -1
        i += 1
    return objects

@st.cache_data(ttl=3600)
def fetch_and_parse_ts():
    all_alternatives = []
    
    for file_name in FILES:
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/src/data/{file_name}"
        try:
            resp = requests.get(url)
            if resp.status_code != 200: continue
            
            blocks = extract_top_level_objects(resp.text)
            
            for block in blocks:
                # --- FLEXIBLER PARSER PRO BLOCK ---
                # 1. Name extrahieren
                name_m = re.search(r'name\s*:\s*[\'"`](.*?)[\'"`]', block)
                if not name_m: continue
                name = name_m.group(1)
                
                # 2. Replaces extrahieren (Array oder String)
                replaces_list = []
                # Sucht nach: replaces: [ ... ]
                rep_match = re.search(r'replaces\s*:\s*\[([\s\S]*?)\]', block)
                if rep_match:
                    replaces_list = re.findall(r'[\'"`](.*?)[\'"`]', rep_match.group(1))
                else:
                    # Fallback: replaces: "string"
                    single_rep = re.search(r'replaces\s*:\s*[\'"`](.*?)[\'"`]', block)
                    if single_rep: replaces_list = [single_rep.group(1)]
                
                # 3. URL extrahieren
                url_m = re.search(r'(?:url|website|link)\s*:\s*[\'"`](.*?)[\'"`]', block, re.IGNORECASE)
                url_val = url_m.group(1) if url_m else ""
                
                all_alternatives.append({
                    "name": name,
                    "replaces": ", ".join(replaces_list),
                    "url": url_val
                })
        except:
            continue
            
    return all_alternatives

# --- UI ---
st.title("🇪🇺 Digitaler Souveränitäts-Check")
st.write("Live-Daten aus dem European Alternatives Projekt.")

data = fetch_and_parse_ts()

if data:
    query = st.text_input("Suche (z.B. OneDrive, Outlook, WhatsApp):", placeholder="Stichwort...")

    if query:
        q = query.lower().strip()
        # Wir durchsuchen jetzt explizit Name UND das Replaces-Feld
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
    st.write("Mitwirkender: coolerfisch")
