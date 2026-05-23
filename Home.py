import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global
inicializar_layout_global()

st.set_page_config(page_title="Painel de Mortalidade", layout="wide")



st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)


data = get_data()
df_ciclos = data["ciclos_vida"]
df_violencia = data["violencia"]

anos_disponiveis = sorted(df_ciclos["ano_obito"].unique())
ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])

st.sidebar.title("📌 Filtros Globais")
st.sidebar.markdown("Estes filtros afetam todas as páginas do painel.")


filtro_anos = st.sidebar.slider(
    "Selecione o Período",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    key="slider_ano_global"
)

sexos_disponiveis = sorted(df_ciclos["sexo"].unique().tolist())
filtro_sexo = st.sidebar.multiselect(
    "Selecione o Gênero",
    options=sexos_disponiveis,
    default=sexos_disponiveis,
    key="multiselect_sexo_global"
)

df_ciclos_filtrado = df_ciclos[
    (df_ciclos["ano_obito"] >= filtro_anos[0]) & 
    (df_ciclos["ano_obito"] <= filtro_anos[1]) &
    (df_ciclos["sexo"].isin(filtro_sexo))
]

df_violencia_filtrado = df_violencia[
    (df_violencia["ano_obito"] >= filtro_anos[0]) & 
    (df_violencia["ano_obito"] <= filtro_anos[1]) &
    (df_violencia["sexo"].isin(filtro_sexo))
]

st.title("📊 Mapeamento Histórico da Mortalidade no Brasil")
st.markdown(f'''Uma análise baseada nos dados do **Sistema de Informações sobre Mortalidade (SIM)** abrangendo o período de {filtro_anos[0]} a {filtro_anos[1]}.
            \nAnálise feita por **Felipe Melo (Ciência de Dados e IA) como pesquisa em conjunto a FUNASA.**''')
st.markdown("---")

total_obitos = df_ciclos_filtrado["total_obitos"].sum()

if total_obitos > 0:
    idade_media = (df_ciclos_filtrado["media_idade_geral"] * df_ciclos_filtrado["total_obitos"]).sum() / total_obitos
else:
    idade_media = 0

total_violencia = df_violencia_filtrado[df_violencia_filtrado["circ_obito"] != "Não Aplicável"]["total_obitos"].sum()
pct_violencia = (total_violencia / total_obitos * 100) if total_obitos > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric(label="Total de Óbitos Analisados", value=f"{total_obitos:,}".replace(",", "."))
col2.metric(label="Idade Média ao Morrer", value=f"{idade_media:.1f} anos")
col3.metric(label="Mortalidade por Causas Externas", value=f"{pct_violencia:.1f}%")

st.markdown("### 📈 Visão Geral Temporal")
col_graph1, col_graph2 = st.columns([2, 1])

with col_graph1:
    df_linha = df_ciclos_filtrado.groupby("ano_obito")["total_obitos"].sum().reset_index()
    fig_linha = px.line(
        df_linha, x="ano_obito", y="total_obitos",
        title="Evolução Anual do Volume Total de Óbitos",
        labels={"ano_obito": "Ano", "total_obitos": "Quantidade de Óbitos"},
        template="plotly_white"
    )
    fig_linha.update_traces(line_color="#1f77b4", line_width=3)
    st.plotly_chart(fig_linha, use_container_width=True)

with col_graph2:
    df_sexo = df_ciclos_filtrado.groupby("sexo")["total_obitos"].sum().reset_index()
    fig_barra = px.bar(
        df_sexo, x="sexo", y="total_obitos",
        title="Distribuição por Gênero",
        labels={"sexo": "Gênero", "total_obitos": "Óbitos Acumulados"},
        color="sexo",
        color_discrete_sequence=["#1f77b4", "#2ca02c", "#7f7f7f"],
        template="plotly_white"
    )
    fig_barra.update_layout(showlegend=False)
    st.plotly_chart(fig_barra, use_container_width=True)