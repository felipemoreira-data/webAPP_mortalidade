import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global

inicializar_layout_global()


st.set_page_config(page_title="Geografia da Mortalidade", layout="wide")


st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
        border-top: 4px solid #00cc96;
    }
    </style>
""", unsafe_allow_html=True)


data = get_data()
df_geo = data["geografia"].copy()


df_geo["ano_obito"] = df_geo["ano_obito"].astype(int)
df_geo["uf"] = df_geo["uf"].fillna("Sem registro").replace({"": "Sem registro", "None": "Sem registro"})


anos_disponiveis = sorted(df_geo["ano_obito"].unique())
ano_min, ano_max = int(anos_disponiveis[0]), int(anos_disponiveis[-1])

if "ciclos_vida" in data:
    sexos_disponiveis = sorted(data["ciclos_vida"]["sexo"].unique().tolist())
else:
    sexos_disponiveis = ["Masculino", "Feminino", "Ignorado"]


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

if len(filtro_sexo) < len(sexos_disponiveis):
    st.sidebar.info("💡 *Nota: Esta base de dados específica do CID-10 é consolidada de forma geral, portanto os gráficos abaixo exibirão o total de ambos os gêneros.*")



st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Qualidade dos Dados")
remover_sem_registro = st.sidebar.checkbox(
    "Ocultar 'Sem registro' dos gráficos", 
    value=False,
    help="Ative para analisar o ranking dos estados ignorando os óbitos que não possuem a UF preenchida."
)


df_filtrado = df_geo[
    (df_geo["ano_obito"] >= filtro_anos[0]) & 
    (df_geo["ano_obito"] <= filtro_anos[1])
].copy()



st.title("🗺️ Geografia e Demografia Espacial da Mortalidade")
st.markdown("""
    > **A Dimensão Territorial:** *Como o volume de óbitos se distribui pelas federações e quais causas (CID-10) predominam em cada região?*

    > ⚠️ **ATENÇÃO:** *Verifique a barra lateral para usar o botão de qualidade dos dados (Ocultação de valores 'Sem Registro')*
""")

st.markdown("---")


total_obitos_geo = df_filtrado["total_obitos"].sum()


total_sem_reg = df_filtrado[df_filtrado["uf"].str.lower() == "sem registro"]["total_obitos"].sum()
pct_sem_reg = (total_sem_reg / total_obitos_geo * 100) if total_obitos_geo > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total de Óbitos Georreferenciados", value=f"{total_obitos_geo:,}".replace(",", "."))
kpi1.caption("Volume absoluto real capturado no período.")

kpi2.metric(label="Notificações sem UF preenchida", value=f"{total_sem_reg:,}".replace(",", "."), delta=f"{pct_sem_reg:.1f}% da base", delta_color="inverse")
kpi2.caption("Dados sem identificação geográfica de estado.")


df_validos = df_filtrado[df_filtrado["uf"].str.lower() != "sem registro"]
if not df_validos.empty:
    top1_uf = df_validos.groupby("uf")["total_obitos"].sum().idxmax()
    top1_qtd = df_validos.groupby("uf")["total_obitos"].sum().max()
    top1_pct = (top1_qtd / total_obitos_geo * 100) if total_obitos_geo > 0 else 0
    kpi3.metric(label=f"🏢 Estado Líder de Notificações", value=f"{top1_uf}", delta=f"{top1_pct:.1f}% do total nacional")
else:
    kpi3.metric(label="Estado Líder", value="N/A")
kpi3.caption("Unidade da Federação com maior volume válido.")

st.markdown("---")


if remover_sem_registro:
    df_graficos = df_filtrado[df_filtrado["uf"].str.lower() != "sem registro"].copy()
else:
    df_graficos = df_filtrado.copy()


col_filtros, col_mapa = st.columns([1, 2])

with col_filtros:
    st.markdown("### 🔍 Lupa Regional por Patologia")
    st.markdown("Escolha um capítulo específico do CID-10 para analisar a distribuição geográfica dos óbitos:")
    
    lista_cid = ["Todos os Capítulos"] + sorted(df_graficos["capitulo_cid"].unique().tolist())
    cid_selecionado = st.selectbox("Selecione o Capítulo CID-10:", lista_cid)
    
    if cid_selecionado != "Todos os Capítulos":
        df_visualizacao = df_graficos[df_graficos["capitulo_cid"] == cid_selecionado]
    else:
        df_visualizacao = df_graficos

    df_ranking_dinamico = df_visualizacao.groupby("uf")["total_obitos"].sum().reset_index()
    df_ranking_dinamico = df_ranking_dinamico.sort_values(by="total_obitos", ascending=False)

with col_mapa:
    st.markdown("### 🌲 Cartografia Proporcional de Óbitos por UF")
    
    if not df_ranking_dinamico.empty and df_ranking_dinamico["total_obitos"].sum() > 0:
        fig_treemap = px.treemap(
            df_ranking_dinamico, path=["uf"], values="total_obitos",
            title=f"Distribuição do Volume de Mortalidade por Estado ({cid_selecionado})",
            color="total_obitos",
            color_continuous_scale="Purples",
            template="plotly_white"
        )
        fig_treemap.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("Sem dados para renderizar o Treemap.")

st.markdown("---")


col_esq, col_dir = st.columns([2, 1])

with col_esq:
    st.markdown("### 🫧 Dispersão Temporal das Unidades da Federação")
    
    df_bolhas = df_visualizacao.groupby(["ano_obito", "uf"])["total_obitos"].sum().reset_index()
    
    if not df_bolhas.empty:
        fig_bubbles = px.scatter(
            df_bolhas, x="ano_obito", y="total_obitos", size="total_obitos", color="uf",
            hover_name="uf",
            title="Trajetória e Peso das UFs ao Longo da Linha do Tempo",
            labels={"ano_obito": "Ano do Óbito", "total_obitos": "Volume de Óbitos", "uf": "Estado (UF)"},
            template="plotly_white"
        )
        fig_bubbles.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_bubbles, use_container_width=True)
    else:
        st.info("Sem dados temporais para esta seleção.")

with col_dir:
    st.markdown("### 📊 Top 10 Estados")
    st.markdown("Ranking do acumulado histórico para a causa selecionada.")
    
    df_top10 = df_ranking_dinamico.head(10).sort_values(by="total_obitos", ascending=True)
    
    if not df_top10.empty:
        fig_top10 = px.bar(
            df_top10, x="total_obitos", y="uf", orientation="h",
            labels={"total_obitos": "Total de Óbitos", "uf": "UF"},
            template="plotly_white"
        )
        fig_top10.update_traces(marker_color="#00cc96")
        fig_top10.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_top10, use_container_width=True)
    else:
        st.info("Sem dados para o ranking.")