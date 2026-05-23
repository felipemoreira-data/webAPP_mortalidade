import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global

inicializar_layout_global()

# 1. Configuração Básica da Página
st.set_page_config(page_title="Violência e Acidentes de Trabalho", layout="wide")

# Re-injetar o estilo dos cards para consistência visual com o restante do app
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

# 2. Carregar Dados da Sessão
data = get_data()
df_violencia = data["violencia"].copy()

# Garantir sincronia de tipos para o filtro de ano funcionar perfeitamente
df_violencia["ano_obito"] = df_violencia["ano_obito"].astype(int)

# Limites dinâmicos para a barra lateral
anos_disponiveis = sorted(df_violencia["ano_obito"].unique())
ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])
sexos_disponiveis = sorted(df_violencia["sexo"].unique().tolist())

# 3. RECRIANDO A SIDEBAR COMPARTILHADA (PERSISTENTE)
st.sidebar.title("📌 Filtros Globais")
st.sidebar.markdown("Estes filtros são compartilhados entre todas as páginas.")

filtro_anos = st.sidebar.slider(
    "Selecione o Período",
    min_value=ano_min,
    max_value=ano_max,
    value=st.session_state.get("slider_ano_global", (ano_min, ano_max)),
    key="slider_ano_global"
)

filtro_sexo = st.sidebar.multiselect(
    "Selecione o Gênero",
    options=sexos_disponiveis,
    default=st.session_state.get("multiselect_sexo_global", sexos_disponiveis),
    key="multiselect_sexo_global"
)

# 4. APLICAR FILTROS HISTÓRICOS
df_filtrado = df_violencia[
    (df_violencia["ano_obito"] >= filtro_anos[0]) & 
    (df_violencia["ano_obito"] <= filtro_anos[1]) &
    (df_violencia["sexo"].isin(filtro_sexo))
].copy()

# 5. TÍTULO DA PÁGINA
st.title("🛡️ Causas Externas: Violência e Acidentes de Trabalho")
st.markdown("> **Pergunta Central de Análise:** *Qual é o impacto das mortes não naturais (homicídios, suicídios e acidentes) na força de trabalho e por gênero?*")
st.markdown("---")

# 6. CÁLCULO DE METRICAS DE TOPO (KPI CARDS)
# Vamos desconsiderar os óbitos "Não Aplicável" para focar puramente em Causas Externas
df_causas_externas = df_filtrado[~df_filtrado["circ_obito"].isin(["Não Aplicável", "Não aplicável", "Ignorado"])]
total_externas = df_causas_externas["total_obitos"].sum()

# Homicídios absolutos e percentuais dentro das causas externas
total_homicidios = df_causas_externas[df_causas_externas["circ_obito"].isin(["Homicídio", "Homicidios", "Agressões"])]["total_obitos"].sum()
pct_homicidios = (total_homicidios / total_externas * 100) if total_externas > 0 else 0

# Acidentes de Trabalho confirmados ("Sim")
total_acid_trab = df_filtrado[df_filtrado["acid_trab"].isin(["Sim", "S"])]["total_obitos"].sum()

# Exibir os KPIs na Tela
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total de Óbitos por Causas Externas", value=f"{total_externas:,}".replace(",", "."))
kpi1.caption("Total de mortes por causas não naturais no período.")
kpi2.metric(label="Óbitos por Homicídio", value=f"{total_homicidios:,}".replace(",", "."), delta=f"{pct_homicidios:.1f}% das C. Externas", delta_color="inverse")
kpi2.caption("Volume absoluto e proporção de mortes violentas intencionais.")
kpi3.metric(label="Acidentes de Trabalho Registrados", value=f"{total_acid_trab:,}".replace(",", "."))
kpi3.caption("Óbitos com notificação positiva para acidente laboral.")

st.markdown("---")

# 7. GRELHA DE GRÁFICOS
row1_col1, row1_col2 = st.columns([1, 1])

with row1_col1:
    # Gráfico 1: Evolução Temporal das Circunstâncias de Óbito
    df_linha_circ = df_causas_externas.groupby(["ano_obito", "circ_obito"])["total_obitos"].sum().reset_index()
    
    fig_linha_circ = px.line(
        df_linha_circ, x="ano_obito", y="total_obitos", color="circ_obito",
        title="Evolução Histórica das Circunstâncias de Óbito (Causas Externas)",
        labels={"ano_obito": "Ano", "total_obitos": "Quantidade de Óbitos", "circ_obito": "Circunstância"},
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig_linha_circ.update_traces(line_width=3)
    st.plotly_chart(fig_linha_circ, use_container_width=True)

with row1_col2:
    # Gráfico 2: Perfil de Gênero nas Causas Externas (Barras Agrupadas)
    df_sexo_circ = df_causas_externas.groupby(["circ_obito", "sexo"])["total_obitos"].sum().reset_index()
    
    fig_barra_circ = px.bar(
        df_sexo_circ, x="circ_obito", y="total_obitos", color="sexo",
        title="Distribuição de Causas Externas por Gênero",
        labels={"circ_obito": "Circunstância do Óbito", "total_obitos": "Volume de Óbitos", "sexo": "Gênero"},
        barmode="group",
        template="plotly_white",
        color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#2ca02c", "Ignorado": "#7f7f7f"}
    )
    st.plotly_chart(fig_barra_circ, use_container_width=True)

st.markdown("### 💼 Radiografia dos Óbitos por Acidente de Trabalho")

# Gráfico 3: Gráfico de barras mostrando a evolução anual dos acidentes de trabalho confirmados por gênero
df_trab_filtro = df_filtrado[df_filtrado["acid_trab"].isin(["Sim", "S"])]
df_linha_trab = df_trab_filtro.groupby(["ano_obito", "sexo"])["total_obitos"].sum().reset_index()

fig_linha_trab = px.bar(
    df_linha_trab, x="ano_obito", y="total_obitos", color="sexo",
    title="Evolução Histórica de Óbitos por Acidente de Trabalho por Gênero",
    labels={"ano_obito": "Ano do Óbito", "total_obitos": "Quantidade de Óbitos Laborais", "sexo": "Gênero"},
    barmode="stack",
    template="plotly_white",
    color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#2ca02c", "Ignorado": "#7f7f7f"}
)
st.plotly_chart(fig_linha_trab, use_container_width=True)