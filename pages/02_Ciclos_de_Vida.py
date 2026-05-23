import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global

inicializar_layout_global()

st.set_page_config(page_title="Mortalidade e Ciclos de Vida", layout="wide")

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
df_ciclos = data["ciclos_vida"].copy()

# Garantir sincronia de tipos
df_ciclos["ano_obito"] = df_ciclos["ano_obito"].astype(int)

# Limites dinâmicos
anos_disponiveis = sorted(df_ciclos["ano_obito"].unique())
ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])
sexos_disponiveis = sorted(df_ciclos["sexo"].unique().tolist())

# 🛠️ RECRIANDO A SIDEBAR SINCRONIZADA COM A HOME
st.sidebar.title("📌 Filtros Globais")
st.sidebar.markdown("Estes filtros são compartilhados entre todas as páginas.")

# Slider conectado à chave global da Home
filtro_anos = st.sidebar.slider(
    "Selecione o Período",
    min_value=ano_min,
    max_value=ano_max,
    value=st.session_state.get("slider_ano_global", (ano_min, ano_max)),
    key="slider_ano_global" # A mesma chave garante que a escolha da Home apareça aqui
)

# Multiselect conectado à chave global da Home
filtro_sexo = st.sidebar.multiselect(
    "Selecione o Gênero",
    options=sexos_disponiveis,
    default=st.session_state.get("multiselect_sexo_global", sexos_disponiveis),
    key="multiselect_sexo_global" # A mesma chave mantém os sexos marcados na Home
)

# Aplicar os filtros na base de dados
df_filtrado = df_ciclos[
    (df_ciclos["ano_obito"] >= filtro_anos[0]) & 
    (df_ciclos["ano_obito"] <= filtro_anos[1]) &
    (df_ciclos["sexo"].isin(filtro_sexo))
].copy()

# Mapeamento para o cálculo ponderado real
mapeamento_idades = {
    "0-1": 0.5, "0 a 1 ano": 0.5, "Menor de 1 ano": 0.5,
    "1-4": 2.5, "5-14": 9.5, "15-29": 22.0, "30-59": 44.5,
    "60-79": 69.5, "80+": 85.0, "80 anos ou mais": 85.0
}
df_filtrado["idade_estimada"] = df_filtrado["faixa_etaria"].map(mapeamento_idades).fillna(45.0)

st.title("👶👵 Ciclos de Vida e Longevidade")
st.markdown("> **Pergunta Central de Análise:** *Com que idade morrem os brasileiros e como evoluiu a longevidade por gênero?*")
st.markdown("---")

total_obitos = df_filtrado["total_obitos"].sum()

if total_obitos > 0:
    df_filtrado["idade_total_ponderada"] = df_filtrado["idade_estimada"] * df_filtrado["total_obitos"]
    idade_media_kpi = df_filtrado["idade_total_ponderada"].sum() / total_obitos
else:
    idade_media_kpi = 0

total_infantil = df_filtrado[df_filtrado["faixa_etaria"].isin(["0-1", "0 a 1 ano", "Menor de 1 ano"])]["total_obitos"].sum()
pct_infantil = (total_infantil / total_obitos * 100) if total_obitos > 0 else 0

total_idosos = df_filtrado[df_filtrado["faixa_etaria"].isin(["60-79", "80+", "60 anos ou mais", "80 anos ou mais"])]["total_obitos"].sum()
pct_idosos = (total_idosos / total_obitos * 100) if total_obitos > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Idade Média Estimada ao Morrer", value=f"{idade_media_kpi:.1f} anos")
kpi2.metric(label="Óbitos Infantis (Menores de 1 ano)", value=f"{total_infantil:,}".replace(",", "."), delta=f"{pct_infantil:.1f}% do total", delta_color="inverse")
kpi3.metric(label="Proporção de Óbitos na Terceira Idade", value=f"{pct_idosos:.1f}%")

st.markdown("---")

row1_col1, row1_col2 = st.columns([1, 1])

with row1_col1:
    if total_obitos > 0:
        df_agrupado_idade = df_filtrado.groupby(["ano_obito", "sexo"]).agg(
            soma_idades_ponderadas=("idade_total_ponderada", "sum"),
            soma_obitos=("total_obitos", "sum")
        ).reset_index()
        
        df_agrupado_idade["idade_media_real"] = df_agrupado_idade["soma_idades_ponderadas"] / df_agrupado_idade["soma_obitos"]
        df_agrupado_idade = df_agrupado_idade[df_agrupado_idade["soma_obitos"] > 0]
        
        fig_linha_idade = px.line(
            df_agrupado_idade, x="ano_obito", y="idade_media_real", color="sexo",
            title="Evolução da Idade Média Real ao Morrer por Gênero",
            labels={"ano_obito": "Ano do Óbito", "idade_media_real": "Idade Média Real (Anos)", "sexo": "Gênero"},
            template="plotly_white",
            color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#2ca02c", "Ignorado": "#7f7f7f"}
        )
        fig_linha_idade.update_traces(line_width=3)
        st.plotly_chart(fig_linha_idade, use_container_width=True)
    else:
        st.info("Sem dados suficientes para gerar as curvas temporais.")

with row1_col2:
    df_barra_faixa = df_filtrado.groupby(["faixa_etaria", "sexo"])["total_obitos"].sum().reset_index()
    ordem_faixas = ["0-1", "1-4", "5-14", "15-29", "30-59", "60-79", "80+"]
    faixas_presentes = [f for f in ordem_faixas if f in df_barra_faixa["faixa_etaria"].unique()]
    
    fig_barra_faixa = px.bar(
        df_barra_faixa, y="faixa_etaria", x="total_obitos", color="sexo",
        orientation="h", barmode="group",
        title="Distribuição Absoluta de Óbitos por Faixa Etária",
        labels={"faixa_etaria": "Faixa Etária", "total_obitos": "Quantidade de Óbitos", "sexo": "Gênero"},
        category_orders={"faixa_etaria": faixas_presentes},
        template="plotly_white",
        color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#2ca02c", "Ignorado": "#7f7f7f"}
    )
    st.plotly_chart(fig_barra_faixa, use_container_width=True)

st.markdown("### 📈 Mudança Estrutural ao Longo do Tempo")
df_area_tempo = df_filtrado.groupby(["ano_obito", "faixa_etaria"])["total_obitos"].sum().reset_index()

fig_area_tempo = px.area(
    df_area_tempo, x="ano_obito", y="total_obitos", color="faixa_etaria",
    title="Evolução do Volume de Óbitos por Faixa Etária Ano a Ano",
    labels={"ano_obito": "Ano", "total_obitos": "Volume de Óbitos", "faixa_etaria": "Faixa Etária"},
    category_orders={"faixa_etaria": faixas_presentes},
    template="plotly_white",
    color_discrete_sequence=px.colors.sequential.Viridis
)
st.plotly_chart(fig_area_tempo, use_container_width=True)