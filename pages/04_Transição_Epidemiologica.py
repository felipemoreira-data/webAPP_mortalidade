import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import get_data
from core.components import inicializar_layout_global

inicializar_layout_global()


st.set_page_config(page_title="Transição Epidemiológica", layout="wide")


st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
        border-left: 5px solid #636efa;
    }
    .fato-historico {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #6c757d;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


data = get_data()
df_transicao = data["transicao"].copy()


df_transicao["ano_obito"] = df_transicao["ano_obito"].astype(int)


anos_disponiveis = sorted(df_transicao["ano_obito"].unique())
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


df_filtrado = df_transicao[
    (df_transicao["ano_obito"] >= filtro_anos[0]) & 
    (df_transicao["ano_obito"] <= filtro_anos[1])
].copy()


if len(filtro_sexo) < len(sexos_disponiveis):
    st.sidebar.info("💡 *Nota: Esta base de dados específica do CID-10 é consolidada de forma geral, portanto os gráficos abaixo exibirão o total de ambos os gêneros.*")


st.title("🦠 A Transição Epidemiológica no Brasil")
st.markdown("""
    > **A Grande Transformação:** Ao longo das últimas décadas, o perfil de mortalidade do Brasil mudou drasticamente. 
    > Deixamos de ser um país cuja principal ameaça eram as doenças infecciosas e parasitárias (típicas de nações jovens e sem saneamento) 
    > para nos tornarmos um país assolado por doenças crônicas e cardiovasculares (reflexo do envelhecimento e da urbanização).
""")
st.markdown("---")


total_obitos_periodo = df_filtrado["total_obitos"].sum()

df_ranking_geral = df_filtrado.groupby("capitulo_cid")["total_obitos"].sum().reset_index()
df_ranking_geral = df_ranking_geral.sort_values(by="total_obitos", ascending=False)

if not df_ranking_geral.empty:
    causa_top1 = df_ranking_geral.iloc[0]["capitulo_cid"]
    qtde_top1 = df_ranking_geral.iloc[0]["total_obitos"]
    pct_top1 = (qtde_top1 / total_obitos_periodo * 100) if total_obitos_periodo > 0 else 0
    
    causa_top2 = df_ranking_geral.iloc[1]["capitulo_cid"] if len(df_ranking_geral) > 1 else "N/A"
    qtde_top2 = df_ranking_geral.iloc[1]["total_obitos"] if len(df_ranking_geral) > 1 else 0
    pct_top2 = (qtde_top2 / total_obitos_periodo * 100) if total_obitos_periodo > 0 else 0
else:
    causa_top1, pct_top1 = "N/A", 0
    causa_top2, pct_top2 = "N/A", 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total de Óbitos Mapeados (CID-10)", value=f"{total_obitos_periodo:,}".replace(",", "."))
kpi2.metric(label=f"🥇 Maior Causa: {causa_top1[:30]}...", value=f"{pct_top1:.1f}%", delta="Líder Histórico")
kpi3.metric(label=f"🥈 2ª Maior Causa: {causa_top2[:30]}...", value=f"{pct_top2:.1f}%")

st.markdown("---")


st.markdown("### 🏃‍♂️ A Corrida das Causas de Morte (Evolução do Top 5)")
st.markdown("Veja como os capítulos do CID-10 subiram ou desceram no ranking de letalidade ano a ano.")

df_filtrado["ranking"] = df_filtrado.groupby("ano_obito")["total_obitos"].rank(method="first", ascending=False)
causas_top5 = df_filtrado[df_filtrado["ranking"] <= 5]["capitulo_cid"].unique()
df_bump = df_filtrado[df_filtrado["capitulo_cid"].isin(causas_top5)].copy()

fig_bump = px.line(
    df_bump, x="ano_obito", y="ranking", color="capitulo_cid",
    markers=True,
    title="Inversão Histórica: Qual patologia tirou mais vidas ao longo dos anos?",
    labels={"ano_obito": "Ano", "ranking": "Posição no Ranking (1º é o mais letal)", "capitulo_cid": "Capítulo CID-10"},
    template="plotly_white"
)
fig_bump.update_yaxes(autorange="reversed", dtick=1)
fig_bump.update_traces(line_width=4, marker=dict(size=10))
st.plotly_chart(fig_bump, use_container_width=True)

st.markdown("---")


col_ctrl, col_graph = st.columns([1, 2])

with col_ctrl:
    st.markdown("### 🔍 Lupa Epidemiológica")
    st.markdown("Escolha um capítulo específico do CID-10 para isolar a sua tendência histórica e ler um insight contextualizado.")
    
    lista_causas = sorted(df_filtrado["capitulo_cid"].unique())
    causa_selecionada = st.selectbox("Selecione a Causa para Isolamento:", lista_causas)
    
    st.markdown("#### 💡 Notas de Contexto:")
    if "aparelho circulatório" in causa_selecionada.lower():
        st.info("📌 **Infartos e AVCs:** Lideram de forma isolada as estatísticas há anos. O avanço reflete o estresse urbano, dietas ultraprocessadas e o envelhecimento natural da pirâmide demográfica.")
    elif "neoplasias" in causa_selecionada.lower() or "tumores" in causa_selecionada.lower():
        st.info("📌 **O Avanço do Câncer:** À medida que a medicina vence doenças infecciosas e as pessoas vivem mais, o câncer ganha espaço proporcional, exigindo novas infraestruturas oncológicas.")
    elif "infecciosas" in causa_selecionada.lower() or "parasitárias" in causa_selecionada.lower():
        st.warning("📌 **Transição Sanitária:** A queda acentuada ao longo dos anos 90 e 2000 é uma vitória direta da expansão do saneamento básico, vacinação em massa e criação do SUS.")
    else:
        st.info("📌 **Análise Temporal:** Use o gráfico ao lado para analisar a estabilidade, crescimento ou recuo deste capítulo ao longo das políticas de saúde pública implementadas nas últimas décadas.")

with col_graph:
    df_isolado = df_filtrado[df_filtrado["capitulo_cid"] == causa_selecionada].sort_values("ano_obito")
    
    fig_isolado = px.area(
        df_isolado, x="ano_obito", y="total_obitos",
        title=f"Curva Histórica Isolada: {causa_selecionada}",
        labels={"ano_obito": "Ano", "total_obitos": "Volume Anual de Óbitos"},
        template="plotly_white"
    )
    fig_isolado.update_traces(line_color="#ef553b", fillcolor="rgba(239, 85, 59, 0.2)")
    st.plotly_chart(fig_isolado, use_container_width=True)


with st.expander("⏳ Linha do Tempo: Grandes Marcos da Saúde Pública no Período"):
    st.markdown("""
    <div class="fato-historico">
        <strong>1996 - Expansão do SUS e Coquetel Anti-HIV:</strong> O Brasil se torna referência mundial ao distribuir gratuitamente o tratamento antirretroviral, alterando a curva de óbitos por doenças infecciosas.
    </div>
    <div class="fato-historico">
        <strong>2003 - Criação do SAMU:</strong> A implementação do atendimento móvel de urgência começa a impactar diretamente a sobrevida de pacientes com infarto agudo do miocárdio e AVC.
    </div>
    <div class="fato-historico">
        <strong>2011 - Plano de Enfrentamento das DANTs:</strong> O Ministério da Saúde lança ações estratégicas voltadas para conter Doenças Crônicas Não Transmissíveis, focando em tabagismo e alimentação.
    </div>
    """, unsafe_allow_html=True)