import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- GESTION DES CLÉS (FAILOVER) ---
def get_model():
    keys = []
    if "GEMINI_API_KEY" in st.secrets: keys.append(st.secrets["GEMINI_API_KEY"])
    if "GEMINI_API_KEY_2" in st.secrets: keys.append(st.secrets["GEMINI_API_KEY_2"])
    
    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    return None

model = get_model()
if not model:
    st.error("⚠️ Toutes les clés sont saturées. Réessaie dans 2 min.")
    st.stop()

# --- MÉMOIRE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "texte_lu" not in st.session_state: st.session_state.texte_lu = ""

st.title("🇯🇵 Mon Coach Japonais")

# --- 1. SCANNER ---
st.subheader("1. Ma Leçon")
fichier = st.file_uploader("Photo du cours", type=['png', 'jpg', 'jpeg'])

if fichier:
    img = Image.open(fichier)
    if st.button("📷 Analyser"):
        with st.spinner("Lecture..."):
            try:
                # Instruction claire pour la mise en page
                prompt_scan = "Extrais le texte. Format impératif : Ligne 1 Japonais (Kanji/Kana), Ligne 2 Romaji. Pas de français."
                res = model.generate_content([prompt_scan, img])
                st.session_state.texte_lu = res.text
                st.success("Texte capturé !")
            except:
                st.error("Erreur lecture.")

if st.session_state.texte_lu:
    st.info(st.session_state.texte_lu)

    # --- 2. PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Stop", key='lecture')
    
    if audio:
        with st.spinner("Analyse..."):
            try:
                prompt = f"Analyse cet audio par rapport au texte : '{st.session_state.texte_lu}'. Note /10 et donne 2 conseils précis en FRANÇAIS."
                res = model.generate_content([prompt, {'mime_type': 'audio/wav', 'data': audio['bytes']}])
                st.markdown("### 💡 Feedback")
                st.write(res.text)
            except:
                st.warning("Erreur audio. Réessaie.")

    # --- 3. DIALOGUE D'IMMERSION (CORRIGÉ) ---
    st.divider()
    st.subheader("3. Discussion avec Nakamura")
    
    # On affiche l'historique
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Bouton pour répondre
    audio_chat = mic_recorder(start_prompt="🎤 Répondre", stop_prompt="🛑 Envoyer", key='chat')

    if audio_chat:
        with st.spinner("Nakamura réfléchit..."):
            try:
                # C'EST ICI QUE TOUT CHANGE : LE PROMPT DE JEU DE RÔLE
                prompt_roleplay = f"""
                CONTEXTE : Nous jouons une scène basée sur ce texte : "{st.session_state.texte_lu}".
                TON RÔLE : Tu es un ami japonais (Nakamura).
                TA MISSION : Discute avec moi. Pose-moi une question simple liée au texte (mon âge, où j'habite, mon nom).
                RÈGLES STRICTES :
                1. Ne fais PAS de résumé. Ne fais PAS le prof.
                2. Fais des phrases courtes et naturelles.
                3. Format : Japonais (Kanji/Kana) puis Romaji en dessous.
                4. PAS DE FRANÇAIS.
                """
                
                # On envoie l'audio et l'historique court
                history_content = [msg["content"] for msg in st.session_state.chat_history[-4:]] # On garde les 4 derniers échanges
                response = model.generate_content([prompt_roleplay] + history_content + [{'mime_type': 'audio/wav', 'data': audio_chat['bytes']}])
                
                # Mise à jour du chat
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Ta réponse vocale)"})
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error("Petit bug de connexion. Réessaie !")

    # Bouton Reset
    if st.button("🔄 Recommencer la discussion"):
        st.session_state.chat_history = []
        st.rerun()
