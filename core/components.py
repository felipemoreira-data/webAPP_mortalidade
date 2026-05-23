# core/ui_components.py
import streamlit as st

def inicializar_layout_global():
    """Injeta o CSS customizado em qualquer página onde for chamada."""
    import os
    caminho_css = "styles/custom.css"
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

