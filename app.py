import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- CONNEXION ---
def get_api_key():
    if "GEMINI_API_KEY_2" in st.secrets: return st.secrets["GEMINI_API_KEY_2"]
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    return None

key = get_api_key()
if not key:
    st.error("⚠️ Clé API manquante.")
    st.stop()

genai.configure(api_key=key)
# On reste sur le modèle qui marche, même s'il est capricieux
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- CERVEAU INTELLIGENT (ANTI-CRASH) ---
def ask_ai_smartly(prompt_content):
    """Essaie d'appeler l'IA. Si ça bloque (quota), attend et réessaie."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_content)
        except Exception as e:
            # Si c'est le dernier essai, on abandonne
            if attempt == max_retries - 1:
                st.error(f"Le Sensei est vraiment KO : {e}")
                return None
            
            # Sinon, on attend un peu (5s, puis 10s...)
            wait_time = (attempt + 1) * 5
            st.toast(f"⏳ Trafic dense... Pause de {wait_time}s", icon="🍵")
            time.sleep(wait_time)
    return None

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    # Bouton protégé contre les clics multiples
    if st.button("📷 Analyser l'image", disabled=(st.session_state.texte_lu != "")):
        with st.spinner("Lecture en cours..."):
            res = ask_ai_smartly([
                "Extrais le texte. Format OBLIGATOIRE : Japonais (Kanji/Kana) en haut, Romaji en dessous. Pas de français.", 
                img
            ])
            if res:
                st.session_state.texte_lu = res.text
                st.success("Texte capturé !")
                st.rerun()

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Analyse de l'accent..."):
            prompt = f"Analyse cet audio pour le texte : '{st.session_state.texte_lu}'. Note /10 et donne 2 conseils précis en FRANÇAIS."
            res = ask_ai_smartly([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
            if res:
                st.markdown("### 💡 Feedback")
                st.write(res.text)

    # --- 3. DIALOGUE D'IMMERSION (JEU DE RÔLE) ---
    st.divider()
    st.subheader("3. Discussion avec Nakamura")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    audio_chat = mic_recorder(start_prompt="🎤 Répondre", stop_prompt="🛑 Envoyer", key='chat')

    if audio_chat:
        with st.spinner("Nakamura t'écoute..."):
            # Prompt Jeu de Rôle (pour éviter le résumé scolaire)
            prompt_roleplay = f"""
            CONTEXTE : JEU DE RÔLE. Tu ES Nakamura (ami japonais).
            SUJET : "{st.session_state.texte_lu}".
            ACTION : Réponds à mon audio de façon naturelle et pose une question courte.
            RÈGLES : Japonais + Romaji uniquement. Pas de français. Pas de résumé.
            """
            
            # On envoie l'historique récent + l'audio
            history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]]
            res = ask_ai_smartly([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
            
            if res:
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse)"})
                st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                st.rerun()

    if st.button("🔄 Recommencer la discussion"):
        st.session_state.chat_history = []
        st.rerun()
