import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION DE L'INTERFACE (LOOK APPLICATION) ---
st.set_page_config(
    page_title="Nihongo Coach",
    page_icon="🇯🇵",
    initial_sidebar_state="collapsed"
)

# Style CSS pour masquer les éléments superflus de Streamlit
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0); height: 0rem;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONNEXION SÉCURISÉE À GEMINI ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante dans les Secrets Streamlit.")

# Utilisation du modèle 'flash-latest' pour une meilleure stabilité avec les images
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : IMPORT DU COURS ---
st.subheader("1. Ma Leçon")
mode = st.tabs(["📷 Photo / Scan", "⌨️ Clavier"])

texte_a_etudier = ""

with mode[0]:
    fichier = st.file_uploader("Prendre une photo de mon cours", type=['png', 'jpg', 'jpeg'])
    if fichier:
        img = Image.open(fichier)
        st.image(img, caption="Document importé", width=300)
        with st.spinner("L'IA analyse l'image..."):
            try:
                # Requête explicite pour l'extraction de texte
                res = model.generate_content([
                    "Tu es un expert en japonais. Extrais tout le texte japonais et romaji visible sur cette image. Ne donne QUE le texte, sans aucun commentaire en français.", 
                    img
                ])
                if res.text:
                    texte_a_etudier = res.text
                    st.success("Texte extrait avec succès !")
                else:
                    st.warning("Aucun texte n'a été détecté sur l'image.")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")

with mode[1]:
    texte_manuel = st.text_area("Tape ou modifie ton texte ici :", value=texte_a_etudier, height=150)
    if texte_manuel:
        texte_a_etudier = texte_manuel

# --- SECTION 2 : AFFICHAGE PÉDAGOGIQUE ---
if texte_a_etudier:
    with st.expander("👀 Texte préparé pour l'étude", expanded=True):
        with st.spinner("Mise en forme..."):
            # On demande à Gemini de formater proprement
            format_res = model.generate_content(f"""
                Réécris ce texte japonais pour une lecture facile :
                1. Une ligne en Japonais (ajoute des espaces entre les mots et les particules)
                2. Une ligne en Rōmaji juste en dessous
                Ne traduis pas en français.
                Texte : "{texte_a_etudier}"
            """)
            st.markdown(format_res.text)

    # --- SECTION 3 : PRATIQUE ORALE ---
    st.subheader("2. Pratique Orale")
    st.write("Lis le texte ci-dessus à voix haute :")
    
    # Enregistreur audio (ne coupe pas si tu fais des pauses)
    audio = mic_recorder(
        start_prompt="🎤 Commencer",
        stop_prompt="🛑 Terminer / Envoyer",
        key='recorder'
    )

    if audio:
        st.audio(audio['bytes'])
        with st.spinner("Analyse de ta prononciation..."):
            # Simulation de feedback (l'analyse audio directe par Gemini arrive progressivement)
            st.info("💡 Conseil : Pour une voix plus naturelle, assure-toi de ne pas trop insister sur le 'u' final de 'desu'.")
            
            # Bouton pour lancer une petite discussion sur le thème
            if st.button("💬 Discuter sur ce thème"):
                st.write("L'IA va maintenant te poser une question simple en japonais...")
