import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION LOOK "APP" ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵", initial_sidebar_state="collapsed")

# Masquage des éléments Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION GEMINI ---
if "GEMINI_API_KEY" in st.secrets:
    # On force l'utilisation de la version stable v1 de l'API pour éviter l'erreur 404
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
else:
    st.error("Clé API manquante dans les Secrets !")

# Utilisation du nom de modèle le plus simple possible
MODEL_NAME = 'gemini-1.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

st.title("🇯🇵 Nihongo Coach")

# --- SECTION 1 : IMPORT DU COURS ---
st.subheader("1. Ma Leçon")
mode = st.tabs(["📷 Scanner", "⌨️ Saisir"])
texte_a_etudier = ""

with mode[0]:
    fichier = st.file_uploader("Capture de ton cours", type=['png', 'jpg', 'jpeg'])
    if fichier:
        img = Image.open(fichier)
        st.image(img, width=300)
        if st.button("Scanner l'image"):
            with st.spinner("Analyse en cours..."):
                try:
                    # On utilise une méthode de génération plus directe
                    response = model.generate_content(
                        contents=["Extrais le texte japonais et romaji de cette image. Texte brut uniquement.", img]
                    )
                    if response.text:
                        st.session_state.texte_extrait = response.text
                        st.success("Texte extrait !")
                except Exception as e:
                    st.error(f"Erreur technique : {e}")
                    st.info("Vérifie que ta clé API n'a pas de restriction de sécurité sur Google Cloud Console.")

    if "texte_extrait" in st.session_state:
        texte_a_etudier = st.session_state.texte_extrait

with mode[1]:
    # On permet la modification manuelle du texte extrait
    texte_manuel = st.text_area("Texte à pratiquer :", value=texte_a_etudier, height=150)
    texte_a_etudier = texte_manuel

# --- SECTION 2 : ÉTUDE ET ORAL ---
if texte_a_etudier:
    with st.expander("📖 Lecture préparée", expanded=True):
        with st.spinner("Mise en forme pédagogique..."):
            try:
                # Formatage en double ligne Japonais / Romaji
                format_res = model.generate_content(f"Réécris ce texte avec une ligne en Japonais (espaces entre les mots) et une ligne en Rōmaji en dessous. Pas de français : {texte_a_etudier}")
                st.markdown(format_res.text)
            except:
                st.write(texte_a_etudier)

    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Parler", stop_prompt="🛑 Stop", key='recorder')

    if audio:
        st.audio(audio['bytes'])
        st.success("Prononciation enregistrée !")
