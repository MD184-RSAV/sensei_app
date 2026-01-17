import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION LOOK "APP" ---
st.set_page_config(
    page_title="Nihongo Coach",
    page_icon="🇯🇵", # Forcer l'icône ici
    initial_sidebar_state="collapsed"
)

# Masquage des menus Streamlit
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
    # On initialise avec le modèle testé dans ton Playground
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé manquante dans Secrets")

# MODÈLE EXACT DE TON TEST RÉUSSI
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : IMPORT DU COURS ---
st.subheader("1. Ma Leçon")
mode = st.tabs(["📷 Scanner", "⌨️ Saisir"])

texte_final = ""

with mode[0]:
    fichier = st.file_uploader("Capture de ton cours", type=['png', 'jpg', 'jpeg'])
    if fichier:
        img = Image.open(fichier)
        st.image(img, width=300)
        if st.button("Lancer l'analyse"):
            with st.spinner("L'IA lit ta photo..."):
                try:
                    # Utilisation de la méthode Gemini 3
                    response = model.generate_content([
                        "Extrais tout le texte japonais et romaji de cette image. Texte brut uniquement.", 
                        img
                    ])
                    st.session_state.texte_lu = response.text
                    st.success("Lecture terminée !")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    if "texte_lu" in st.session_state:
        texte_final = st.session_state.texte_lu

with mode[1]:
    texte_final = st.text_area("Texte à pratiquer :", value=texte_final, height=150)

# --- SECTION 2 : ÉTUDE ET ORAL ---
if texte_final:
    with st.expander("📖 Lecture préparée (Japonais / Romaji)", expanded=True):
        try:
            format_res = model.generate_content(f"Réécris ce texte avec une ligne en Japonais (espaces entre les mots) et une ligne en Rōmaji : {texte_final}")
            st.markdown(format_res.text)
        except:
            st.write(texte_final)

    st.subheader("2. Pratique Orale")
    mic_recorder(start_prompt="🎤 Parler", stop_prompt="🛑 Stop", key='recorder')
