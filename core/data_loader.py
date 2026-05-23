import streamlit as st
import pandas as pd
import os
import numpy as np

@st.cache_data
def carregar_resumos():
    caminho_base = "data/"

    files = {
        'ciclos_vida': 'resumo_ciclos_vida.parquet',
        'desigualdade': 'resumo_desigualdade.parquet',
        'geografia': 'resumo_geografia.parquet',
        'transicao': 'resumo_transicao.parquet',
        'violencia': 'resumo_violencia.parquet'
    }
    
    dataframes = {}

    for key, filename in files.items():
        path = os.path.join(caminho_base, filename)
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                if 'ano_obito' in df.columns:
                    df['ano_obito'] = pd.to_numeric(df['ano_obito'], errors='coerce').fillna(0).astype(int)
                dataframes[key] = df
            except Exception as e:
                st.error(f'Erro ao carregar {filename}: {e}')
                dataframes[key] = pd.DataFrame()
        else:
            dataframes[key] = pd.DataFrame()
            st.error(f'Arquivo não encontrado: {filename}')

    return dataframes    

def get_data():
    """
    Retorna os dados armazenados no session state e garante 
    que as colunas essenciais estejam presentes, evitando erros 
    de 'key not found'. Retorna 'Sem Registro' ou np.nan para dados ausentes.
    """
    if 'df_sim' not in st.session_state:
        with st.spinner('Carregando os dados de mortalidade (SIM)...'):
            st.session_state.df_sim = carregar_resumos()

    return st.session_state.df_sim
