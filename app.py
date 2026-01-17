import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION LOOK "APP" ---
st.set_page_config(
    page_title="Nihongo Coach", 
    page_icon="🇯🇵", 
    initial_sidebar_state="collapsed"
)

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
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Configure ta clé API dans les Secrets de Streamlit !")

# Changement ici : On utilise 'models/gemini-1.5-flash-latest' pour plus de compatibilité
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.title("🇯🇵 Nihongo Coach")

# --- SECTION 1 : ENTRÉE DU TEXTE ---
st.subheader("1. Ma Leçon")
mode = st.tabs(["📷 Scanner", "⌨️ Saisir"])
texte_a_etudier = ""

with mode[0]:
    fichier = st.file_uploader("Prends ton cours en photo", type=['png', 'jpg', 'jpeg'])
    if fichier:
        img = Image.open(fichier)
        st.image(img, width=300)
        if st.button("Scanner l'image"):
            with st.spinner("L'IA analyse la photo..."):
                try:
                    # Envoi structuré : texte + image
                    response = model.generate_content([
                        "Extrais tout le texte japonais et romaji de cette image. Ne donne que le texte brut, sans commentaires.",
                        img
                    ])
                    if response.text:
                        # On stocke le résultat dans la session pour qu'il reste affiché
                        st.session_state.texte_extrait = response.text
                        st.success("Texte extrait !")
                except Exception as e:
                    st.error(f"Erreur d'IA : {e}")

    # Récupération du texte extrait si disponible
    if "texte_extrait" in st.session_state:
        texte_a_etudier = st.session_state.texte_extrait

with mode[1]:
    texte_manuel = st.text_area("Texte à pratiquer :", value=texte_a_etudier, height=150)
    texte_a_etudier = texte_manuel

# --- SECTION 2 : ÉTUDE ET ORAL ---
if texte_a_etudier:
    with st.expander("📖 Lecture préparée", expanded=True):
        with st.spinner("Formatage..."):
            format_res = model.generate_content(f"Réécris ce texte avec une ligne en Japonais (espaces entre les mots) et une ligne en Rōmaji en dessous. Pas de français : {texte_a_etudier}")
            st.markdown(format_res.text)

    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Parler", stop_prompt="🛑 Stop", key='recorder')

    if audio:
        st.audio(audio['bytes'])
        st.info("💡 Prononciation reçue !")
