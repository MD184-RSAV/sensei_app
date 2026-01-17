import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- CONNEXION INTELLIGENTE ---
def get_api_key():
    if "GEMINI_API_KEY_2" in st.secrets: return st.secrets["GEMINI_API_KEY_2"]
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    return None

key = get_api_key()
if not key:
    st.error("⚠️ Clé API manquante.")
    st.stop()

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- CERVEAU ANTI-CRASH ---
def ask_ai_smartly(prompt_content):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_content)
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"Le Sensei est KO : {e}")
                return None
            wait_time = (attempt + 1) * 5
            st.toast(f"⏳ Trafic dense... Pause de {wait_time}s", icon="🍵")
            time.sleep(wait_time)
    return None

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""
# NOUVEAU : État pour savoir si la conversation est finie
if "conversation_active" not in st.session_state: st.session_state.conversation_active = True

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    if st.button("📷 Analyser l'image", disabled=(st.session_state.texte_lu != "")):
        with st.spinner("Lecture..."):
            res = ask_ai_smartly([
                "Extrais le texte. Format : Japonais (Kanji/Kana) en haut, Romaji en dessous. Pas de français.", 
                img
            ])
            if res:
                st.session_state.texte_lu = res.text
                st.session_state.chat_history = [] # On reset le chat si on scanne un nouveau texte
                st.session_state.conversation_active = True
                st.rerun()

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Analyse..."):
            prompt = f"Analyse cet audio pour le texte : '{st.session_state.texte_lu}'. Note /10 et donne 2 conseils précis en FRANÇAIS."
            res = ask_ai_smartly([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
            if res:
                st.markdown("### 💡 Feedback")
                st.write(res.text)

    # --- 3. DIALOGUE D'IMMERSION ---
    st.divider()
    st.subheader("3. Discussion avec Nakamura")
    
    # Affichage de l'historique
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Zone de contrôle de la conversation
    if st.session_state.conversation_active:
        col1, col2 = st.columns([3, 1]) # Colonnes pour aligner les boutons
        
        with col1:
            st.write("À toi de répondre :")
            audio_chat = mic_recorder(start_prompt="🎤 Parler", stop_prompt="🛑 Envoyer", key='chat')
        
        with col2:
            st.write("Option :")
            if st.button("🏁 Terminer"):
                with st.spinner("Nakamura vous salue..."):
                    # On demande à l'IA de dire au revoir
                    prompt_bye = f"Le contexte était : {st.session_state.texte_lu}. L'utilisateur doit partir. Dis-lui au revoir chaleureusement en Japonais + Romaji."
                    res_bye = ask_ai_smartly([prompt_bye])
                    if res_bye:
                        st.session_state.chat_history.append({"role": "assistant", "content": res_bye.text})
                        st.session_state.conversation_active = False # On désactive le micro
                        st.rerun()

        # Logique de réponse audio standard
        if audio_chat:
            with st.spinner("Nakamura t'écoute..."):
                prompt_roleplay = f"""
                CONTEXTE : JEU DE RÔLE. Tu ES Nakamura. SUJET : "{st.session_state.texte_lu}".
                ACTION : Réponds naturellement. Question courte.
                RÈGLES : Japonais + Romaji uniquement. Pas de français.
                """
                history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]]
                res = ask_ai_smartly([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
                
                if res:
                    st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse)"})
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    st.rerun()
    
    else:
        # Si la conversation est finie
        st.success("Conversation terminée ! Otsukaresama desu ! (Beau travail !)")
        if st.button("🔄 Recommencer une discussion"):
            st.session_state.chat_history = []
            st.session_state.conversation_active = True
            st.rerun()
