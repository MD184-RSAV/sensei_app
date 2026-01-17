import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")

# Masquage Streamlit
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;}</style>", unsafe_allow_html=True)

# --- CONNEXION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante dans les Secrets.")

model = genai.GenerativeModel('gemini-3-flash-preview')

# Initialisation de la mémoire
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "texte_lu" not in st.session_state:
    st.session_state.texte_lu = ""

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    if st.button("📷 Analyser l'image"):
        with st.spinner("Lecture..."):
            res = model.generate_content(["Extrais le texte japonais/romaji de cette image.", img])
            st.session_state.texte_lu = res.text

if st.session_state.texte_lu:
    with st.expander("📖 Voir le texte extrait", expanded=False):
        st.write(st.session_state.texte_lu)

    # --- SECTION 2 : ANALYSE ORALE (AVEC CONSEILS EN FRANÇAIS) ---
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Analyser mon accent", key='recorder_lecture')

    if audio:
        with st.spinner("Analyse du Sensei..."):
            audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
            # Ici, on autorise le français pour la pédagogie
            prompt_accent = f"""
            Analyse mon audio pour ce texte : '{st.session_state.texte_lu}'. 
            1. Donne une note sur 10.
            2. Donne des conseils de prononciation détaillés EN FRANÇAIS pour m'aider à m'améliorer.
            """
            feedback = model.generate_content([prompt_accent, audio_part])
            st.info(feedback.text)

    # --- SECTION 3 : DIALOGUE INTERACTIF (IMMERSION JAPONAIS/ROMAJI) ---
    st.divider()
    st.subheader("3. Dialogue d'immersion")
    st.write("Ici, le Sensei ne parle que japonais !")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    audio_chat = mic_recorder(start_prompt="🎤 Répondre au Sensei", stop_prompt="🛑 Envoyer", key='recorder_chat')

    if audio_chat:
        with st.spinner("Le Sensei réfléchit..."):
            audio_msg = {"mime_type": "audio/wav", "data": audio_chat['bytes']}
            
            # Ici, interdiction du français pour le flux de conversation
            prompt_context = f"""
            Tu es un prof de japonais. On discute autour de ce texte : {st.session_state.texte_lu}. 
            Réponds à l'élève et pose-lui une question simple.
            RÈGLE : Interdiction d'utiliser le français. 
            Réponds uniquement en Japonais (Kanji/Kana) avec le Rōmaji juste en dessous.
            """
            
            response = model.generate_content([prompt_context] + [msg["content"] for msg in st.session_state.chat_history] + [audio_msg])
            
            st.session_state.chat_history.append({"role": "user", "content": "🎤 (Message vocal)"})
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            
            st.rerun()

    if st.button("🔄 Nouveau dialogue"):
        st.session_state.chat_history = []
        st.rerun()
