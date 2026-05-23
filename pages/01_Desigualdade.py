import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global

inicializar_layout_global()



st.set_page_config(page_title="Desigualdades Sociodemográficas", layout="wide")


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
df_desigualdade = data["desigualdade"]


if "total obitos" in df_desigualdade.columns:
    col_obitos = "total obitos"
elif "total_obitos" in df_desigualdade.columns:
    col_obitos = "total_obitos"
else:
    
    col_obitos = df_desigualdade.select_dtypes(include=['number']).columns[0]


anos_disponiveis = sorted(df_desigualdade["ano_obito"].unique())
ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])


filtro_anos = st.sidebar.slider(
    "Selecione o Período", min_value=ano_min, max_value=ano_max, 
    value=(ano_min, ano_max), key="desig_slider"
)
sexos_disponiveis = df_desigualdade["sexo"].unique().tolist()
filtro_sexo = st.sidebar.multiselect(
    "Selecione o Gênero", options=sexos_disponiveis, 
    default=sexos_disponiveis, key="desig_sexo"
)


df_filtrado = df_desigualdade[
    (df_desigualdade["ano_obito"] >= filtro_anos[0]) & 
    (df_desigualdade["ano_obito"] <= filtro_anos[1]) &
    (df_desigualdade["sexo"].isin(filtro_sexo))
]


st.title("📍 Desigualdades Sociodemográficas na Mortalidade")
st.markdown("> **Pergunta Central de Análise:** *Quem morre e em que condições sociais no Brasil?*")
st.markdown("Esta secção analisa o impacto dos fatores de raça/cor e os níveis de instrução (escolaridade) nas estatísticas históricas de óbitos.")
st.markdown("---")


total_periodo = df_filtrado[col_obitos].sum()


df_raca_total = df_filtrado.groupby("raca_cor")[col_obitos].sum().reset_index()
total_negros = df_raca_total[df_raca_total["raca_cor"].isin(["Preta", "Parda"])][col_obitos].sum()
pct_negros = (total_negros / total_periodo * 100) if total_periodo > 0 else 0


df_esc_total = df_filtrado.groupby("esc")[col_obitos].sum().reset_index()
baixa_instrucao = df_esc_total[df_esc_total["esc"].isin(["Nenhuma", "Sem escolaridade", "1 a 3 anos"])][col_obitos].sum()
pct_baixa_esc = (baixa_instrucao / total_periodo * 100) if total_periodo > 0 else 0


kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Óbitos Filtrados nesta Aba", value=f"{total_periodo:,}".replace(",", "."))
kpi1.caption("Soma total no intervalo e géneros escolhidos.")
kpi2.metric(label="Proporção de Pretos e Pardos", value=f"{pct_negros:.1f}%")
kpi2.caption("Óbitos autodeclarados como raça Preta ou Parda.")
kpi3.metric(label="Baixa Escolaridade / Sem Instrução", value=f"{pct_baixa_esc:.1f}%")
kpi3.caption("Óbitos com histórico de 0 a 3 anos de estudo.")

st.markdown("---")


row1_col1, row1_col2 = st.columns([1, 1])

with row1_col1:
    
    df_linha_raca = df_filtrado.groupby(["ano_obito", "raca_cor"])[col_obitos].sum().reset_index()
    fig_linha_raca = px.line(
        df_linha_raca, x="ano_obito", y=col_obitos, color="raca_cor",
        title="Evolução Temporal Histórica por Raça/Cor",
        labels={"ano_obito": "Ano do Óbito", col_obitos: "Volume de Óbitos", "raca_cor": "Raça/Cor"},
        template="plotly_white"
    )
    st.plotly_chart(fig_linha_raca, use_container_width=True)

with row1_col2:
    
    fig_donut_raca = px.pie(
        df_raca_total, values=col_obitos, names="raca_cor", hole=0.4,
        title="Composição Percentual por Raça/Cor no Período",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_donut_raca, use_container_width=True)

st.markdown("### 🎓 Impacto do Nível de Instrução por Gênero")


df_esc_clean = df_filtrado[~df_filtrado["esc"].isin(["Ignorado", "Não Aplicável", "Sem Registro"])]
df_barra_esc = df_esc_clean.groupby(["esc", "sexo"])[col_obitos].sum().reset_index()

ordem_escolaridade = [
    "Nenhuma", "Sem escolaridade", "1 a 3 anos", "Fundamental I (1ª a 4ª série)", 
    "4 a 7 anos", "Fundamental II (5ª a 8ª série)", "8 a 11 anos", "Ensino Médio", 
    "Superior incompleto", "12 anos e mais", "Superior completo"
]
categorias_presentes = [cat for cat in ordem_escolaridade if cat in df_barra_esc["esc"].unique()]

fig_barra_esc = px.bar(
    df_barra_esc, x="esc", y=col_obitos, color="sexo",
    title="Volume de Óbitos por Nível de Escolaridade e Gênero",
    labels={"esc": "Nível de Escolaridade", col_obitos: "Total de Óbitos", "sexo": "Gênero"},
    category_orders={"esc": categorias_presentes},
    barmode="stack",
    template="plotly_white",
    color_discrete_sequence=["#1f77b4", "#aec7e8", "#ffbb78"]
)
st.plotly_chart(fig_barra_esc, use_container_width=True)