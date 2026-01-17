import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")

# Look "App"
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;}</style>", unsafe_allow_html=True)

# --- CONNEXION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante dans les Secrets.")

# On utilise Gemini 3 Flash qui est performant mais on va limiter les appels
model = genai.GenerativeModel('gemini-3-flash-preview')

# Initialisation de la mémoire
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "texte_lu" not in st.session_state:
    st.session_state.texte_lu = ""

st.title("🇯🇵 Mon Coach Japonais")

# --- SECTION 1 : SCANNER (Optimisé) ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    # On n'affiche le bouton que si on n'a pas encore de texte pour économiser le quota
    if st.button("📷 Analyser l'image"):
        with st.spinner("Lecture du texte japonais..."):
            try:
                res = model.generate_content([
                    "Tu es un expert en japonais. Extrais le texte. "
                    "Affiche : 1. Japonais (Kanjis/Kanas) avec espaces. "
                    "2. Romaji en dessous. Pas de français.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.success("Lecture terminée !")
            except Exception as e:
                st.error("Quota atteint ou erreur. Attends 1 minute et réessaie.")

if st.session_state.texte_lu:
    st.markdown("### 📝 Ma Leçon")
    st.info(st.session_state.texte_lu)

    # --- SECTION 2 : PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Analyser mon accent", key='recorder_lecture')

    if audio:
        with st.spinner("Le Sensei écoute..."):
            try:
                audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
                prompt_accent = f"Analyse mon audio pour ce texte : '{st.session_state.texte_lu}'. Note sur 10 et conseils EN FRANÇAIS."
                feedback = model.generate_content([prompt_accent, audio_part])
                st.markdown("#### 💡 Feedback")
                st.write(feedback.text)
            except:
                st.warning("Trop de requêtes. Attends un instant avant de demander un nouveau feedback.")

    # --- SECTION 3 : DIALOGUE (Optimisé pour le quota) ---
    st.divider()
    st.subheader("3. Dialogue d'immersion")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    audio_chat = mic_recorder(start_prompt="🎤 Répondre au Sensei", stop_prompt="🛑 Envoyer", key='recorder_chat')

    if audio_chat:
        with st.spinner("Le Sensei réfléchit..."):
            try:
                audio_msg = {"mime_type": "audio/wav", "data": audio_chat['bytes']}
                prompt_context = f"Tu es un prof de japonais. On parle de : {st.session_state.texte_lu}. Réponds brièvement en Japonais+Romaji uniquement. Pas de français."
                
                response = model.generate_content([prompt_context] + [msg["content"] for msg in st.session_state.chat_history[-2:]] + [audio_msg])
                
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Vocal)"})
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except:
                st.error("Le Sensei est fatigué (Quota épuisé). Réessaie dans quelques minutes.")

    if st.button("🔄 Nouveau dialogue"):
        st.session_state.chat_history = []
        st.rerun()
