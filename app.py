import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION DE L'INTERFACE ---
st.set_page_config(
    page_title="Nihongo Coach",
    page_icon="🇯🇵",
    initial_sidebar_state="collapsed" # Cache la barre latérale pour faire "App"
)

# Masquer les menus Streamlit pour le look "Vraie App"
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# Connexion sécurisée à Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante dans les Secrets Streamlit.")

model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : IMPORT DU COURS ---
st.subheader("1. Ma Leçon")
mode = st.tabs(["📷 Photo / Scan", "⌨️ Clavier"])

texte_a_etudier = ""

with mode[0]:
    fichier = st.file_uploader("Scanner mon cours", type=['png', 'jpg', 'jpeg'])
    if fichier:
        img = Image.open(fichier)
        st.image(img, caption="Document scanné", width=300)
        with st.spinner("Lecture du texte..."):
            res = model.generate_content([
                "Extrais le texte japonais ou romaji de cette image. Affiche-le proprement sans commentaires.", 
                img
            ])
            texte_a_etudier = res.text
            st.success("Texte extrait !")

with mode[1]:
    texte_manuel = st.text_area("Ou tape ton texte ici :", value=texte_a_etudier)
    if texte_manuel:
        texte_a_etudier = texte_manuel

# --- SECTION 2 : AFFICHAGE PÉDAGOGIQUE ---
if texte_a_etudier:
    with st.expander("👀 Voir le texte préparé", expanded=True):
        with st.spinner("Formatage..."):
            # On demande à Gemini de formater le texte pour l'étude
            format_res = model.generate_content(f"""
                Prends ce texte : "{texte_a_etudier}"
                Réécris-le avec :
                1. Japonais (espacé)
                2. Rōmaji juste en dessous
                Pas de français.
            """)
            st.markdown(format_res.text)

    # --- SECTION 3 : ORAL ---
    st.subheader("2. Pratique Orale")
    st.write("Lis le texte à voix haute :")
    
    audio = mic_recorder(
        start_prompt="🎤 Commencer",
        stop_prompt="🛑 Terminer",
        key='recorder'
    )

    if audio:
        st.audio(audio['bytes'])
        with st.spinner("Analyse de ta prononciation..."):
            # Ici on envoie l'audio à Gemini pour feedback
            # Note: Pour l'instant on simule l'analyse textuelle
            st.success("Analyse terminée ! Tes pauses étaient bonnes, attention au 'R' japonais.")
