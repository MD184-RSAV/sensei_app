import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import io
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Nihongo Speak", page_icon="🗣️")
st.markdown("<style>.stDeployButton {display:none;} .block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# --- CONNEXION OPENAI ---
if "OPENAI_API_KEY" not in st.secrets:
    st.error("⚠️ Clé OpenAI manquante dans les Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- FONCTIONS UTILES ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# --- INTERFACE ---
st.title("🗣️ Nihongo Speak")
st.write("Scanne ton texte et pratique ta prononciation avec GPT-4o.")

if "current_text" not in st.session_state:
    st.session_state.current_text = ""

# --- 1. LE SCANNER ---
with st.expander("📷 Étape 1 : Scanner mon texte", expanded=(st.session_state.current_text == "")):
    uploaded_file = st.file_uploader("Prends ton manuel en photo", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file and st.button("Lire l'image"):
        with st.spinner("Analyse par GPT-4o..."):
            try:
                base64_image = encode_image(uploaded_file)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extrais le texte japonais de cette image. Affiche le texte en Kanji/Kana, puis une transcription en Romaji juste en dessous de chaque phrase. Pas de français."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                )
                st.session_state.current_text = response.choices[0].message.content
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- 2. LA PRATIQUE ---
if st.session_state.current_text:
    st.subheader("📖 Texte à pratiquer")
    st.info(st.session_state.current_text)
    
    st.divider()
    st.subheader("🎤 Étape 2 : S'enregistrer")
    st.write("Lis le texte à voix haute :")
    
    audio = mic_recorder(
        start_prompt="🔴 Commencer l'enregistrement",
        stop_prompt="⏹️ Arrêter",
        key='recorder'
    )

    if audio:
        with st.spinner("Analyse de ta prononciation..."):
            try:
                # 1. Transcription de ton audio via Whisper
                audio_bio = io.BytesIO(audio['bytes'])
                audio_bio.name = "audio.wav"
                
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bio,
                    language="ja"
                )
                
                st.write(f"**Ce que l'IA a entendu :** {transcript.text}")
                
                # 2. Feedback avec GPT-4o
                feedback_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Tu es un sensei de japonais bienveillant."},
                        {"role": "user", "content": f"Le texte cible était : {st.session_state.current_text}. L'élève a dit : {transcript.text}. Donne une note de prononciation sur 10 et 2 conseils courts en français pour s'améliorer."}
                    ]
                )
                
                st.markdown("### 💡 Feedback du Sensei")
                st.write(feedback_response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse audio : {e}")

    if st.button("🧹 Effacer et recommencer"):
        st.session_state.current_text = ""
        st.rerun()
