import streamlit as st
import requests

# Konfiguration des Repositories
REPO_OWNER = "TheMorpheus407"
REPO_NAME = "european-alternatives"
API_TREE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/"

st.set_page_config(page_title="European Alternatives Navigator", layout="wide")

# Lade-Funktion mit Caching (Daten werden 1 Stunde gespeichert)
@st.cache_data(ttl=3600)
def indexiere_repository():
    try:
        # 1. Rufe den kompletten Verzeichnisbaum des Repositories ab
        tree_response = requests.get(API_TREE_URL)
        if tree_response.status_code != 200:
            return []
        
        tree = tree_response.json().get("tree", [])
        
        # 2. Filtere alle Markdown-Dateien (ausser Templates)
        md_files = [f["path"] for f in tree if f["path"].endswith(".md") and "ISSUE" not in f["path"]]
        
        alle_eintraege = []
        
        # 3. Lade jede Datei herunter und parse die Inhalte
        for file_path in md_files:
            raw_url = RAW_BASE_URL + file_path
            file_resp = requests.get(raw_url)
            
            if file_resp.status_code == 200:
                content = file_resp.text
                kategorie = file_path.split("/")[-1].replace(".md", "").capitalize()
                
                # Sehr toleranter Parser fuer Markdown-Tabellen
                lines = content.split("\n")
                for line in lines:
                    # Suche nach Tabellenzeilen (enthalten '|')
                    if "|" in line and "---" not in line and "Alternative" not in line:
                        # Spalten extrahieren und leere bereinigen
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        
                        # Eine gueltige Datenzeile hat meist mindestens 2 Spalten
                        if len(parts) >= 2:
                            alle_eintraege.append({
                                "Name": parts[0],
                                "Details": " | ".join(parts[1:]),
                                "Kategorie": kategorie,
                                "Datei": file_path
                            })
                            
        return alle_eintraege
    except Exception as e:
        st.error(f"Fehler beim Indexieren: {e}")
        return []

# App Interface
st.title("Digitaler Souveraenitaets-Navigator")
st.write("Diese App indexiert live das gesamte GitHub-Repository und macht alle Tabellen durchsuchbar.")

# Daten laden
datenbank = indexiere_repository()

if not datenbank:
    st.warning("Lade Daten oder das Repository ist gerade nicht erreichbar...")
else:
    # Suchfeld
    suchbegriff = st.text_input("Dienst oder Stichwort suchen (z.B. WhatsApp, Cloud, Mail):", placeholder="Suchbegriff eingeben...").lower()
    
    if suchbegriff:
        # Durchsuche alle extrahierten Felder nach dem Begriff
        treffer = [d for d in datenbank if suchbegriff in d["Name"].lower() or suchbegriff in d["Details"].lower() or suchbegriff in d["Kategorie"].lower()]
        
        if treffer:
            st.success(f"{len(treffer)} Ergebnisse gefunden:")
            for t in treffer:
                with st.container():
                    st.markdown(f"**{t['Name']}** (Kategorie: {t['Kategorie']})")
                    st.write(f"Infos & Links: {t['Details']}")
                    st.caption(f"Gefunden in: {t['Datei']}")
                    st.write("---")
        else:
            # Der "Joerg-Filter" greift auch hier weiterhin
            if "telegram" in suchbegriff:
                st.error("Telegram ist gemaess der Projekt-Kriterien nicht gelistet (Sitz in Dubai, proprietärer Server-Code).")
                st.write("Wir empfehlen stattdessen: Threema oder Session.")
            else:
                st.info("Kein direkter Treffer. Eventuell wurde dieser Dienst noch nicht in die Tabellen aufgenommen.")

# Seitenleiste
with st.sidebar:
    st.header("Über das Tool")
    st.write("Dieses Tool durchsucht automatisch ALLE Markdown-Dateien im Repository nach eingetragenen Alternativen.")
    st.write("---")
    st.write(f"Datenquelle: [{REPO_OWNER}/{REPO_NAME}](https://github.com/{REPO_OWNER}/{REPO_NAME})")
    st.write("Mitwirkender: coolerfisch")