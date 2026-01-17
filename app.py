import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- FONCTION DE CONNEXION INTELLIGENTE ---
def get_api_key():
    # On cherche une clé valide parmi celles dispo
    keys = []
    if "GEMINI_API_KEY" in st.secrets: keys.append(st.secrets["GEMINI_API_KEY"])
    if "GEMINI_API_KEY_2" in st.secrets: keys.append(st.secrets["GEMINI_API_KEY_2"])
    
    # On retourne la première clé trouvée (on suppose qu'elle marche pour le 1.5 Flash)
    if keys: return keys[0]
    return None

api_key = get_api_key()

if not api_key:
    st.error("⚠️ Aucune clé API trouvée dans les Secrets.")
    st.stop()
else:
    genai.configure(api_key=api_key)

# --- LES DEUX CERVEAUX ---
# Cerveau 1 : L'Expert Visuel (Limité mais puissant)
model_scan = genai.GenerativeModel('gemini-3-flash-preview')

# Cerveau 2 : Le Prof Bavard (Robuste et quasi illimité)
model_chat = genai.GenerativeModel('gemini-1.5-flash')

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER (Utilise Gemini 3) ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    if st.button("📷 Analyser (Gemini 3)"):
        with st.spinner("L'expert déchiffre l'image..."):
            try:
                # On utilise model_scan ICI SEULEMENT
                prompt_scan = "Extrais le texte. Format impératif : Ligne 1 Japonais (Kanji/Kana), Ligne 2 Romaji. Pas de français."
                res = model_scan.generate_content([prompt_scan, img])
                st.session_state.texte_lu = res.text
                st.success("Texte capturé !")
            except Exception as e:
                st.error(f"Erreur scan (Si Quota, attends 1 min): {e}")

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE (Utilise Gemini 1.5) ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Analyse..."):
            try:
                prompt = f"Analyse cet audio par rapport au texte : '{st.session_state.texte_lu}'. Note /10 et donne 2 conseils précis en FRANÇAIS."
                # On utilise model_chat (1.5 Flash) pour l'audio, c'est beaucoup plus sûr pour le quota
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

    audio_chat = mic_recorder(start_prompt="🎤 Répondre", stop_prompt="🛑 Envoyer", key='chat')

    if audio_chat:
        with st.spinner("Nakamura réfléchit..."):
            try:
                prompt_roleplay = f"""
                CONTEXTE : JEU DE RÔLE basé sur : "{st.session_state.texte_lu}".
                RÔLE : Tu es l'ami japonais (Nakamura).
                ACTION : Réponds à mon audio et pose une nouvelle question courte.
                RÈGLES : 
                1. Phrases courtes et naturelles (style oral).
                2. Format : Japonais (Kanji) + Romaji.
                3. Zéro français.
                """
                
                # On utilise model_chat (1.5 Flash) ici aussi !
                history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]]
                response = model_chat.generate_content([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
                
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse)"})
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error("Erreur connexion. Réessaie.")

    if st.button("🔄 Recommencer"):
        st.session_state.chat_history = []
        st.rerun()
