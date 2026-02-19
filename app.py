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
            
            # Teile den gesamten Text an jedem "name:" auf (Multizeilen-Modus)
            # Dadurch haben wir für jeden Dienst einen sauberen, isolierten Textblock
            blocks = re.split(r'(?m)^\s*(?:["\']?name["\']?)\s*:\s*', content)
            
            for block in blocks[1:]: # Der erste Block ist nur Datei-Kopf, den überspringen wir
                
                # 1. Name extrahieren (steht jetzt immer ganz am Anfang des Blocks)
                name_match = re.search(r'^([\'"`])(.*?)\1', block)
                if not name_match:
                    continue
                name = name_match.group(2).strip()
                
                # 2. Replaces (Array) extrahieren
                replaces_str = ""
                rep_match = re.search(r'["\']?replaces["\']?\s*:\s*\[(.*?)\]', block, re.DOTALL)
                if rep_match:
                    items = re.findall(r'[\'"`](.*?)[\'"`]', rep_match.group(1))
                    replaces_str = ", ".join(items)
                
                # 3. Beschreibung extrahieren (extrem fehlertolerant)
                # Sucht nach description, desc, notes, info oder details
                desc_str = "Keine Beschreibung verfügbar."
                
                # Variante A: Text in Anführungszeichen/Backticks (auch über mehrere Zeilen)
                desc_match = re.search(r'(?:description|desc|notes|info|details)\s*:\s*([\'"`])(.*?)\1', block, re.DOTALL | re.IGNORECASE)
                if desc_match:
                    # Zeilenumbrüche durch Leerzeichen ersetzen für sauberes Layout
                    raw_desc = desc_match.group(2)
                    desc_str = re.sub(r'\s+', ' ', raw_desc).strip()
                else:
                    # Variante B: Text ohne direkte Anführungszeichen (z.B. hinter einer Funktion)
                    alt_match = re.search(r'(?:description|desc|notes|info|details)\s*:\s*(.*?)[,\n]', block, re.IGNORECASE)
                    if alt_match:
                        raw_val = alt_match.group(1).strip()
                        # Falls es ein Funktionsaufruf wie t("...") ist, ziehen wir den Text heraus
                        t_match = re.search(r'[\'"`](.*?)[\'"`]', raw_val)
                        if t_match:
                            desc_str = t_match.group(1).strip()
                        elif raw_val:
                            desc_str = raw_val

                # 4. URL / Website / Link extrahieren
                url_str = ""
                url_match = re.search(r'(?:url|website|link)\s*:\s*([\'"`])(.*?)\1', block, re.IGNORECASE)
                if url_match:
                    url_str = url_match.group(2).strip()
                
                # In Datenbank aufnehmen
                all_alternatives.append({
                    "name": name,
                    "replaces": replaces_str,
                    "description": desc_str,
                    "url": url_str
                })

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
                    
                    if r.get('url'):
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
