import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import json
import os

# --- CONFIGURATION & STYLE ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵", layout="wide")
st.markdown("""
    <style>
    .stDeployButton {display:none;} 
    .block-container {padding-top: 1rem;}
    /* Style pour les cartes */
    .stExpander {border: 1px solid #e0e0e0; border-radius: 10px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- 1. GESTION DES CLÉS & MODÈLES (ROULETTE) ---
def get_api_key():
    if "GEMINI_API_KEY_2" in st.secrets: return st.secrets["GEMINI_API_KEY_2"]
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    return None

key = get_api_key()
if not key:
    st.error("⚠️ Clé API introuvable.")
    st.stop()

genai.configure(api_key=key, transport='rest')

def get_model():
    # On teste plusieurs modèles pour éviter les blocages
    models = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash-exp']
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model
        except: continue
    return None

if "cached_model" not in st.session_state:
    st.session_state.cached_model = get_model()
model = st.session_state.cached_model

# --- 2. SYSTÈME DE SAUVEGARDE (JSON) ---
VOCAB_FILE = "vocabulaire.json"

def load_vocab():
    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_vocab(new_list):
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(new_list, f, ensure_ascii=False, indent=4)

# Chargement au démarrage
if "vocab_list" not in st.session_state:
    st.session_state.vocab_list = load_vocab()


# --- 3. PAGE : PRONONCIATION ---
def page_prononciation():
    st.header("🗣️ Atelier Prononciation")
    st.caption("Scanne un texte, lis-le, et reçois un feedback immédiat.")

    if "scan_prononciation" not in st.session_state: st.session_state.scan_prononciation = ""

    # Étape 1 : Le Scan
    fichier = st.file_uploader("1. Photo du texte à lire", type=['png', 'jpg', 'jpeg'], key="uploader_pron")
    if fichier:
        img = Image.open(fichier)
        if st.button("📷 Analyser le texte"):
            with st.spinner("Lecture..."):
                try:
                    res = model.generate_content(["Extrais le texte japonais exact.", img])
                    st.session_state.scan_prononciation = res.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # Étape 2 : L'Exercice
    if st.session_state.scan_prononciation:
        st.info(st.session_state.scan_prononciation)
        
        st.write("---")
        st.write("👇 **Enregistre ta lecture :**")
        audio = mic_recorder(start_prompt="🎤 Commencer", stop_prompt="🛑 Stop", key='recorder_pron')
        
        if audio:
            with st.spinner("Le Sensei analyse ton accent..."):
                try:
                    prompt = f"Analyse cet audio par rapport au texte : '{st.session_state.scan_prononciation}'. Note /10 et donne 3 conseils précis en français."
                    res = model.generate_content([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
                    st.success("Analyse terminée !")
                    st.markdown(res.text)
                except Exception as e:
                    st.warning(f"Erreur audio : {e}")

# --- 4. PAGE : VOCABULAIRE ---
def page_vocabulaire():
    st.header("📚 Mon Vocabulaire & Flashcards")
    st.caption(f"Tu as actuellement **{len(st.session_state.vocab_list)} cartes** dans ta collection.")

    # Onglets pour organiser cette page
    tab1, tab2, tab3 = st.tabs(["➕ Ajouter (Scan)", "✍️ Ajouter (Manuel)", "🧠 Réviser"])

    # --- ONGLET 1 : SCAN PHOTO ---
    with tab1:
        st.write("Prends en photo une liste de vocabulaire de ton manuel.")
        fichier_vocab = st.file_uploader("Photo de la liste", type=['png', 'jpg', 'jpeg'], key="uploader_vocab")
        
        if fichier_vocab:
            img_vocab = Image.open(fichier_vocab)
            if st.button("✨ Générer les cartes depuis la photo"):
                with st.spinner("Extraction magique..."):
                    try:
                        # Prompt spécial JSON pour créer les cartes
                        prompt = """
                        Analyse cette image. Extrais TOUS les mots de vocabulaire visibles.
                        Pour chaque mot, crée un objet JSON :
                        {"jap": "Mot en Kanji", "kana": "Lecture Kana", "fr": "Traduction"}
                        Renvoie UNIQUEMENT une liste JSON stricte.
                        """
                        res = model.generate_content([prompt, img_vocab])
                        clean_json = res.text.replace("```json", "").replace("```", "").strip()
                        new_words = json.loads(clean_json)
                        
                        # Ajout et sauvegarde
                        st.session_state.vocab_list.extend(new_words)
                        save_vocab(st.session_state.vocab_list)
                        st.success(f"✅ {len(new_words)} mots ajoutés !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur d'extraction : {e}")

    # --- ONGLET 2 : AJOUT MANUEL ---
    with tab2:
        with st.form("ajout_manuel"):
            col1, col2 = st.columns(2)
            mot_jap = col1.text_input("Japonais (Kanji/Kana)")
            mot_fr = col2.text_input("Français")
            submitted = st.form_submit_button("Ajouter la carte")
            
            if submitted and mot_jap and mot_fr:
                # On demande à l'IA de compléter le Kana manquant
                res_kana = model.generate_content(f"Donne juste la lecture en Hiragana/Katakana de : {mot_jap}")
                nouvelle_carte = {"jap": mot_jap, "kana": res_kana.text.strip(), "fr": mot_fr}
                
                st.session_state.vocab_list.append(nouvelle_carte)
                save_vocab(st.session_state.vocab_list)
                st.success(f"Carte '{mot_jap}' ajoutée !")
                st.rerun()

    # --- ONGLET 3 : RÉVISION ---
    with tab3:
        if not st.session_state.vocab_list:
            st.info("Ta liste est vide. Ajoute des mots d'abord !")
        else:
            st.write("Clique sur une carte pour voir la réponse.")
            # Affichage grille
            cols = st.columns(2)
            for i, carte in enumerate(st.session_state.vocab_list):
                col = cols[i % 2]
                with col:
                    # L'expander sert de carte recto-verso
                    with st.expander(f"🇯🇵 **{carte.get('jap', '???')}**"):
                        st.markdown(f"""
                        - 🗣️ **{carte.get('kana', '')}**
                        - 🇫🇷 {carte.get('fr', '')}
                        """)
            
            if st.button("🗑️ Tout effacer (Attention !)"):
                st.session_state.vocab_list = []
                save_vocab([])
                st.rerun()

# --- 5. MENU DE NAVIGATION (SIDEBAR) ---
with st.sidebar:
    st.title("🇯🇵 Nihongo Coach")
    st.write("---")
    choice = st.radio("Menu", ["Prononciation", "Vocabulaire"])
    
    st.write("---")
    st.caption("Version 2.0 - Multi-pages")
    # Petit indicateur de statut du modèle
    if "cached_model" in st.session_state:
        st.success("IA Connectée 🟢")

# --- 6. ROUTAGE ---
if choice == "Prononciation":
    page_prononciation()
elif choice == "Vocabulaire":
    page_vocabulaire()
