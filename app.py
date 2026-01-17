import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- CONNEXION (AVEC CORRECTIF 404) ---
def get_api_key():
    if "GEMINI_API_KEY_2" in st.secrets: return st.secrets["GEMINI_API_KEY_2"]
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    return None

key = get_api_key()
if not key:
    st.error("⚠️ Clé API manquante.")
    st.stop()

# L'option transport='rest' est la clé pour éviter les erreurs 404 sur Gemini 1.5
genai.configure(api_key=key, transport='rest')

# --- LES DEUX CERVEAUX ---
# 1. Le Scanner (Gemini 3) : Puissant mais capricieux (Quota limité)
model_scan = genai.GenerativeModel('gemini-3-flash-preview')

# 2. Le Bavard (Gemini 1.5) : Robuste et endurant (Pour le chat et l'audio)
model_chat = genai.GenerativeModel('gemini-1.5-flash')

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""
if "conversation_active" not in st.session_state: st.session_state.conversation_active = True

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER (Utilise Gemini 3) ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    # Bouton protégé : on ne re-clique pas si on a déjà le texte
    if st.button("📷 Analyser l'image", disabled=(st.session_state.texte_lu != "")):
        with st.spinner("Lecture experte (Gemini 3)..."):
            try:
                res = model_scan.generate_content([
                    "Extrais le texte. Format OBLIGATOIRE : Japonais (Kanji/Kana) en haut, Romaji en dessous. Pas de français.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.session_state.chat_history = []
                st.session_state.conversation_active = True
                st.rerun()
            except Exception as e:
                st.error(f"Le Scanner est fatigué (Quota). Attends 1 min. ({e})")

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE (Utilise Gemini 1.5) ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Analyse de l'accent (Gemini 1.5)..."):
            try:
                prompt = f"Analyse cet audio pour le texte : '{st.session_state.texte_lu}'. Note /10 et donne 2 conseils précis en FRANÇAIS."
                # On utilise model_chat ici pour économiser le quota du scanner
                res = model_chat.generate_content([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
                st.markdown("### 💡 Feedback")
                st.write(res.text)
            except Exception as e:
                st.warning(f"Erreur audio : {e}")

    # --- 3. DIALOGUE D'IMMERSION (Utilise Gemini 1.5) ---
    st.divider()
    st.subheader("3. Discussion avec Nakamura")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.conversation_active:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            audio_chat = mic_recorder(start_prompt="🎤 Parler", stop_prompt="🛑 Envoyer", key='chat')
        
        with col2:
            st.write("Option :")
            if st.button("🏁 Finir"):
                with st.spinner("Sayonara..."):
                    try:
                        prompt_bye = f"Contexte: {st.session_state.texte_lu}. Dis au revoir poliment en Japonais + Romaji."
                        res_bye = model_chat.generate_content(prompt_bye)
                        st.session_state.chat_history.append({"role": "assistant", "content": res_bye.text})
                        st.session_state.conversation_active = False
                        st.rerun()
                    except:
                        st.session_state.conversation_active = False
                        st.rerun()

        if audio_chat:
            with st.spinner("Nakamura t'écoute..."):
                try:
                    prompt_roleplay = f"""
                    RÔLE : Tu es Nakamura. SUJET : "{st.session_state.texte_lu}".
                    ACTION : Réponds à l'audio, sois naturel, pose une question courte.
                    RÈGLES : Japonais + Romaji. Zéro français.
                    """
                    history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]]
                    # On utilise model_chat ici aussi !
                    res = model_chat.generate_content([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
                    
                    st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse)"})
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur connexion : {e}")

    else:
        st.success("Conversation terminée ! 🎌")
        if st.button("🔄 Recommencer"):
            st.session_state.chat_history = []
            st.session_state.conversation_active = True
            st.rerun()
