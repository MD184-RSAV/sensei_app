import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# Configuration de la page
st.set_page_config(page_title="Mon Coach Japonais", page_icon="🇯🇵")

# Récupération de la clé API
st.title("🇯🇵 Mon Compagnon d'Étude")

# Zone pour entrer ta leçon
st.header("1. Ma leçon du jour")
texte_input = st.text_area("Colle ici ton texte (Rōmaji ou Japonais) :", placeholder="Ex: Hajimemashite, watashi wa Lisa desu...")

if texte_input:
    st.info("Texte enregistré ! Prête pour l'oral ?")

# Zone pour l'oral
st.header("2. Pratique Orale")
st.write("Lis ton texte à voix haute en restant appuyé sur le bouton :")

# Le bouton magique qui ne coupe pas !
audio = mic_recorder(
    start_prompt="🎤 Commencer l'enregistrement",
    stop_prompt="🛑 Arrêter",
    key='recorder'
)

if audio:
    st.audio(audio['bytes'])
    st.success("Audio bien reçu. (On ajoutera l'analyse automatique à l'étape suivante !)")
