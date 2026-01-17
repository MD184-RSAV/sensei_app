import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION INTERFACE ---
st.set_page_config(
    page_title="Nihongo Coach",
    page_icon="🇯🇵",
    initial_sidebar_state="collapsed"
)

# Look "Vraie App"
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
    st.error("Clé API manquante dans les Secrets Streamlit.")

# ON UTILISE LA VERSION 3 COMME DANS TON TEST RÉUSSI
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : LE SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Prends ton cours en photo", type=['png', 'jpg', 'jpeg'])

# On utilise la session_state pour garder le texte en mémoire
if "texte_lu" not in st.session_state:
    st.session_state.texte_lu = ""

if fichier:
    img = Image.open(fichier)
    if st.button("📷 Lancer l'analyse de l'image"):
        with st.spinner("Lecture par l'IA..."):
            try:
                # Extraction du texte
                res = model.generate_content([
                    "Tu es un expert en japonais. Extrais tout le texte japonais et romaji de cette image. Texte brut uniquement.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.success("Image lue !")
            except Exception as e:
                st.error(f"Erreur scan : {e}")

# Affichage du texte et guide de lecture
if st.session_state.texte_lu:
    texte_final = st.text_area("Texte détecté :", value=st.session_state.texte_lu, height=100)
    
    with st.expander("📖 Guide de lecture (Japonais / Romaji)", expanded=True):
        if "guide" not in st.session_state or st.button("Mettre à jour le guide"):
            res_guide = model.generate_content(f"Réécris ce texte avec une ligne Japonais (espaces) et une ligne Romaji en dessous : {texte_final}")
            st.session_state.guide = res_guide.text
        st.markdown(st.session_state.guide)

    # --- SECTION 2 : ANALYSE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    st.write("Enregistre-toi en lisant le texte ci-dessus :")
    
    audio = mic_recorder(
        start_prompt="🎤 Parler", 
        stop_prompt="🛑 Stop & Analyser mon accent", 
        key='recorder'
    )

    if audio:
        st.audio(audio['bytes'])
        with st.spinner("Le Sensei écoute ta voix..."):
            try:
                # Envoi de l'audio à Gemini 3 pour feedback
                audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
                prompt = f"""
                Analyse mon audio par rapport à ce texte : "{texte_final}".
                1. Donne une note de prononciation sur 10.
                2. Dis-moi quels mots j'ai bien prononcé et où je dois m'améliorer.
                3. Donne-moi un conseil pour sonner plus comme un Japonais.
                Réponds de façon sympa en français.
                """
                feedback = model.generate_content([prompt, audio_part])
                
                st.markdown("### 📝 Feedback du Sensei")
                st.write(feedback.text)
                
            except Exception as e:
                st.error(f"L'IA n'a pas pu analyser l'audio : {e}")

    # --- SECTION 3 : CONVERSATION ---
    st.divider()
    if st.button("💬 Lancer une discussion sur ce thème"):
        with st.spinner("Préparation..."):
            conv = model.generate_content(f"En te basant sur ce texte : {texte_final}, pose-moi une question simple en japonais (avec Romaji) pour démarrer une conversation.")
            st.info(conv.text)
