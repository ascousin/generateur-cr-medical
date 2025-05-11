import streamlit as st
import fitz  # PyMuPDF
import io
import openai
from docx import Document

st.set_page_config(page_title="Générateur de compte-rendus médicaux", layout="centered")
st.title("🩺 Générateur de compte-rendus médicaux")

openai_api_key = st.text_input("Clé API OpenAI", type="password")
uploaded_note = st.file_uploader("Sélectionnez une note médicale (PDF)", type=["pdf"])
generate_btn = st.button("Générer le compte-rendu")

# Chargement des exemples (ex1, ex2) 
def get_examples():
    examples = []
    for i in [1, 2]:
        with open(f"ex{i}_note.pdf", "rb") as f:
            note_text = extract_text_from_pdf(f)
        with open(f"ex{i}_cr.docx", "rb") as f:
            cr_text = extract_text_from_docx(f)
        examples.append((note_text, cr_text))
    return examples

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(docx_file):
    document = Document(docx_file)
    texte = ""
    for p in document.paragraphs:
        texte += p.text + "\n"
    return texte

def generate_prompt(examples, new_note):
    prompt = "Voici des exemples de transformation de notes médicales en textes de compte-rendu :\n\n"
    for i, (note, cr) in enumerate(examples):
        prompt += f"Exemple {i+1} - Note :\n{note}\nCompte-rendu :\n{cr}\n\n"
    prompt += "Voici une nouvelle note à transformer :\n"
    prompt += new_note
    prompt += "\n\nMerci de rédiger uniquement le texte principal du compte-rendu, sans en-tête, nom, date ni signature."
    return prompt

if generate_btn and uploaded_note and openai_api_key:
    with st.spinner("Lecture de la note et génération..."):
        examples = get_examples()
        note_text = extract_text_from_pdf(uploaded_note)
        prompt = generate_prompt(examples, note_text)

        try:
            openai.api_key = openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result = response.choices[0].message["content"].strip()

            st.success("Compte-rendu généré !")
            st.subheader("📝 Résultat")
            st.text_area("Texte du compte-rendu", result, height=300)

            # Générer fichier docx
            doc = Document()
            doc.add_paragraph(result)
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="📂 Télécharger en .docx",
                data=buffer,
                file_name="compte_rendu.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
