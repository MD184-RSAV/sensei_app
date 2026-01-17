import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Coach", page_icon="🇯🇵")

# Look "App" propre
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .reportview-container .main .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

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
        with st.spinner("Lecture du texte japonais..."):
            try:
                # On demande explicitement Kanjis + Romaji
                res = model.generate_content([
                    "Tu es un expert en japonais. Extrais le texte de cette image. "
                    "Affiche d'abord la version originale en Japonais (Kanjis/Kanas), "
                    "puis juste en dessous la version en Rōmaji. Pas de français.", 
                    img
                ])
                st.session_state.texte_lu = res.text
                st.success("Lecture terminée !")
            except Exception as e:
                st.error(f"Erreur de lecture : {e}")

if st.session_state.texte_lu:
    # Mise en page soignée du texte extrait
    st.markdown("### 📝 Texte de la leçon")
    st.info(st.session_state.texte_lu)

    # --- SECTION 2 : PRATIQUE ORALE ---
    st.divider()
    st.subheader("2. Pratique Orale")
    st.write("Conseils en Français 🇫🇷 | Dialogue en Japonais 🇯🇵")
    
    audio = mic_recorder(start_prompt="🎤 Lire le texte", stop_prompt="🛑 Analyser mon accent", key='recorder_lecture')

    if audio:
        with st.spinner("Le Sensei écoute..."):
            try:
                audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
                prompt_accent = f"""
                Analyse mon audio pour ce texte : '{st.session_state.texte_lu}'. 
                1. Donne une note sur 10.
                2. Donne des conseils de prononciation détaillés EN FRANÇAIS.
                """
                feedback = model.generate_content([prompt_accent, audio_part])
                st.markdown("#### 💡 Feedback du Sensei")
                st.write(feedback.text)
            except Exception as e:
                st.error(f"Erreur analyse : {e}")

    # --- SECTION 3 : DIALOGUE D'IMMERSION ---
    st.divider()
    st.subheader("3. Dialogue d'immersion")
    
    # Affichage de l'historique
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    audio_chat = mic_recorder(start_prompt="🎤 Répondre au Sensei", stop_prompt="🛑 Envoyer", key='recorder_chat')

    if audio_chat:
        with st.spinner("Le Sensei réfléchit..."):
            try:
                audio_msg = {"mime_type": "audio/wav", "data": audio_chat['bytes']}
                prompt_context = f"""
                Tu es un prof de japonais. On discute autour de ce texte : {st.session_state.texte_lu}. 
                Réponds brièvement à l'élève et pose une question simple.
                RÈGLE : Pas de français. Uniquement Japonais (Kanjis/Kanas) + Rōmaji.
                """
                
                response = model.generate_content([prompt_context] + [msg["content"] for msg in st.session_state.chat_history] + [audio_msg])
                
                st.session_state.chat_history.append({"role": "user", "content": "🎤 (Message vocal)"})
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"Erreur dialogue : {e}")

    if st.button("🔄 Nouveau dialogue"):
        st.session_state.chat_history = []
        st.rerun()
