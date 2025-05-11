import streamlit as st
import fitz  # PyMuPDF
import openai
import os
from docx import Document
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Générateur de compte-rendus médicaux", page_icon="🩺")
st.title("🩺 Générateur de compte-rendus médicaux")

# Clé API
openai_api_key = st.text_input("Clé API OpenAI", type="password")

# Upload fichier PDF
uploaded_file = st.file_uploader("Sélectionnez une note médicale (PDF)", type=["pdf"])

# Lire un fichier PDF temporairement
def extract_text_from_pdf(file_bytes) -> str:
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    os.remove(tmp_path)
    return text

# Exemples locaux (lecture correcte des fichiers)
EXEMPLES = [
    {
        "note_path": "ex1_note.pdf",
        "cr_path": "ex1_cr.docx"
    },
    {
        "note_path": "ex2_note.pdf",
        "cr_path": "ex2_cr.docx"
    }
]

# Formatage des exemples
def format_examples():
    exemples = []
    for ex in EXEMPLES:
        with open(ex["note_path"], "rb") as f:
            note_bytes = f.read()
        note_text = extract_text_from_pdf(note_bytes)
        cr_text = "\n".join([p.text for p in Document(ex["cr_path"]).paragraphs])
        exemples.append((note_text, cr_text))
    return exemples

# Générer le prompt
def build_prompt(exemples, new_note_text):
    prompt = "Voici des exemples de transformation de notes médicales en texte de compte-rendu :\n\n"
    for i, (note, cr) in enumerate(exemples):
        prompt += f"Exemple {i+1} – Note :\n{note}\nCompte-rendu :\n{cr}\n\n"
    prompt += "Voici une nouvelle note à transformer :\n"
    prompt += new_note_text
    prompt += "\n\nMerci de rédiger uniquement le texte principal du compte-rendu, sans en-tête, nom, date ni signature."
    return prompt

# Bouton de génération
if st.button("Générer le compte-rendu"):
    if not uploaded_file:
        st.error("Veuillez sélectionner un fichier PDF.")
    elif not openai_api_key:
        st.error("Veuillez renseigner votre clé API OpenAI.")
    else:
        try:
            file_bytes = uploaded_file.read()
            note_text = extract_text_from_pdf(file_bytes)
            exemples = format_examples()
            prompt = build_prompt(exemples, note_text)

            openai.api_key = openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result = response.choices[0].message["content"].strip()
            st.success("Compte-rendu généré :")
            st.text_area("Résultat", result, height=400)
        except Exception as e:
            st.error(f"Erreur lors de la génération : {str(e)}")
