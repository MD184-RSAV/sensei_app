import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")

st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;}</style>", unsafe_allow_html=True)

# --- SYSTÈME DE CONNEXION DOUBLE CLÉ ---
def get_model():
    # Liste des clés disponibles dans tes secrets
    keys = []
    if "GEMINI_API_KEY" in st.secrets:
        keys.append(st.secrets["GEMINI_API_KEY"])
    if "GEMINI_API_KEY_2" in st.secrets:
        keys.append(st.secrets["GEMINI_API_KEY_2"])

    # On essaie la première clé, si elle sature, on passe à la seconde
    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            # Test léger pour vérifier si la clé répond
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model, i + 1
        except Exception:
            if i == len(keys) - 1: # Si c'est la dernière clé et qu'elle échoue
                return None, 0
            continue
    return None, 0

# Initialisation du modèle
model, key_index = get_model()

if not model:
    st.error("🚫 Toutes vos clés API sont saturées. Attendez 1 minute.")
    st.stop()
else:
    # Petit indicateur discret pour savoir quelle clé est utilisée
    st.caption(f"Connecté via Clé #{key_index}")

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
        with st.spinner("Lecture du texte..."):
            try:
                res = model.generate_content([
                    "Extrais le texte japonais. Format : 1. Japonais (Kanjis/Kanas) 2. Romaji. Pas de français.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.success("Lecture terminée !")
            except Exception as e:
                st.error("Erreur technique. Réessayez dans un instant.")

if st.session_state.texte_lu:
    st.markdown("### 📝 Texte Extrait")
    st.info(st.session_state.texte_lu)

    # --- SECTION 2 : PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Analyser mon accent", key='recorder_lecture')

    if audio:
        with st.spinner("Analyse du Sensei..."):
            try:
                audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
                prompt_accent = f"Analyse cet audio pour le texte : '{st.session_state.texte_lu}'. Note/10 et conseils en Français."
                feedback = model.generate_content([prompt_accent, audio_part])
                st.markdown("#### 💡 Feedback")
                st.write(feedback.text)
            except:
                st.warning("Quota atteint. Réessayez dans 30 secondes.")

    # --- SECTION 3 : DIALOGUE ---
    st.divider()
    st.subheader("3. Dialogue d'immersion")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    audio_chat = mic_recorder(start_prompt="🎤 Répondre", stop_prompt="🛑 Envoyer", key='recorder_chat')

    if audio_chat:
        with st.spinner("Réflexion..."):
            try:
                audio_msg = {"mime_type": "audio/wav", "data": audio_chat['bytes']}
                prompt_ctx = f"Tu es prof. On parle de : {st.session_state.texte_lu}. Réponds en Japonais+Romaji uniquement."
                # On limite l'historique aux 2 derniers messages pour économiser les ressources
                response = model.generate_content([prompt_ctx] + [msg["content"] for msg in st.session_state.chat_history[-2:]] + [audio_msg])
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Vocal)"})
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except:
                st.error("Le Sensei a besoin d'une pause (Quota).")

    if st.button("🔄 Nouveau dialogue"):
        st.session_state.chat_history = []
        st.rerun()
