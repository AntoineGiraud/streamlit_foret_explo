import streamlit as st


st.set_page_config(page_title="Exploration de forêt (placettes)", page_icon="🌳", layout="wide")

with open("README.md", "r", encoding="utf-8") as file:
    readme_contents = file.read()
    st.markdown(readme_contents.replace("# ", "## "), unsafe_allow_html=True)
