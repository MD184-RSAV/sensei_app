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
    # On vérifie toutes les clés possibles
    if "GEMINI_API_KEY_2" in st.secrets: return st.secrets["GEMINI_API_KEY_2"]
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    return None

key = get_api_key()
if not key:
    st.error("⚠️ Clé API manquante. Vérifie tes Secrets.")
    st.stop()

# L'ASTUCE REST : Indispensable pour éviter les erreurs 404 sur mobile
genai.configure(api_key=key, transport='rest')

# LE SAUVEUR : On utilise Gemini 2.0 Flash (Version Expérimentale)
# Il est gratuit, rapide et possède un quota séparé.
MODEL_NAME = 'gemini-2.0-flash-exp'
model = genai.GenerativeModel(MODEL_NAME)

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""
if "conversation_active" not in st.session_state: st.session_state.conversation_active = True

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    # On protège le bouton pour ne pas cliquer 2 fois
    if st.button("📷 Analyser l'image", disabled=(st.session_state.texte_lu != "")):
        with st.spinner("Analyse avec Gemini 2.0..."):
            try:
                # Prompt précis pour le format
                res = model.generate_content([
                    "Tu es un expert japonais. Extrais le texte de l'image. "
                    "Format STRICT : Une ligne en Japonais (Kanji/Kana), puis une ligne en Romaji juste en dessous. "
                    "Fais ça pour chaque phrase. Pas de français.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.session_state.chat_history = []
                st.session_state.conversation_active = True
                st.rerun()
            except Exception as e:
                st.error(f"Erreur technique : {e}")
                st.info("Astuce : Si ça bloque, attends 1 minute ou change de clé API.")

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Le Sensei t'écoute..."):
            try:
                # Gemini 2.0 est excellent en audio
                prompt = f"Écoute cet audio. Texte cible : '{st.session_state.texte_lu}'. Donne une note /10 et 2 conseils de prononciation EN FRANÇAIS."
                res = model.generate_content([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
                st.markdown("### 💡 Feedback")
                st.write(res.text)
            except Exception as e:
                st.warning(f"Problème audio : {e}")

    # --- 3. DIALOGUE D'IMMERSION ---
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
                with st.spinner("Fermeture..."):
                    try:
                        prompt_bye = f"Contexte: {st.session_state.texte_lu}. Dis au revoir poliment en Japonais + Romaji."
                        res_bye = model.generate_content(prompt_bye)
                        st.session_state.chat_history.append({"role": "assistant", "content": res_bye.text})
                        st.session_state.conversation_active = False
                        st.rerun()
                    except:
                        st.session_state.conversation_active = False
                        st.rerun()

        if audio_chat:
            with st.spinner("Nakamura répond..."):
                try:
                    # Prompt "Jeu de rôle"
                    prompt_roleplay = f"""
                    RÔLE : Tu es Nakamura (ami). CONTEXTE : "{st.session_state.texte_lu}".
                    TACHE : Réponds à l'audio de façon naturelle et courte. Pose une question simple.
                    FORMAT : Japonais (Kanji) + Romaji. Zéro français.
                    """
                    
                    # On envoie l'historique récent pour garder le fil
                    history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]]
                    res = model.generate_content([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
                    
                    st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse)"})
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Oups : {e}")
    else:
        if st.button("🔄 Recommencer"):
            st.session_state.chat_history = []
            st.session_state.conversation_active = True
            st.rerun()
