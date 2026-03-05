import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Painel de Tarefas",
    page_icon="📋",
    layout="wide",
)

# ── Estilo minimalista ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.6rem !important; font-weight: 700 !important; }
    .stMetric { background: #f8f8f6; border-radius: 8px; padding: 12px 16px; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; }
    div[data-testid="stMetricDelta"] { font-size: 0.75rem; }
    .section-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin: 1.2rem 0 0.4rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Cores por status ──────────────────────────────────────────────────────────
COR_STATUS = {
    "finalizada":           "#2ECC71",
    "Finalizada em atraso": "#E74C3C",
    "atrasada":             "#F39C12",
    "A fazer":              "#3498DB",
}

LABEL_STATUS = {
    "finalizada":           "Finalizada",
    "Finalizada em atraso": "Em atraso",
    "atrasada":             "Atrasada",
    "A fazer":              "A fazer",
}

# ── Carregamento de dados ─────────────────────────────────────────────────────
@st.cache_data
def carregar(arquivo):
    df = pd.read_excel(arquivo)
    df["Usuário"] = df["Usuário"].fillna("Sem usuário")
    df["Empresa"] = df["Empresa"].fillna("Sem empresa")
    df["Usuario_curto"] = df["Usuário"].apply(
        lambda x: " ".join(
            x.replace("Operador ", "").replace("Gestor ", "").split()[:2]
        )
    )
    df["Empresa_curta"] = df["Empresa"].apply(
        lambda x: " ".join(x.split()[:2])
    )
    return df

# ── Upload ou arquivo padrão ──────────────────────────────────────────────────
st.title("📋 Painel de Tarefas")

with st.sidebar:
    st.header("Dados")
    arquivo = st.file_uploader("Carregar Excel (.xlsx)", type=["xlsx"])
    st.caption("Substitua o arquivo para atualizar o painel.")

if arquivo is None:
    st.info("⬅️ Faça upload do arquivo Excel na barra lateral para começar.")
    st.stop()

df = carregar(arquivo)

# ── Filtros na sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.header("Filtros")

    usuarios = ["Todos"] + sorted(df["Usuario_curto"].unique().tolist())
    filtro_usuario = st.selectbox("Funcionário", usuarios)

    empresas = ["Todas"] + sorted(df["Empresa_curta"].unique().tolist())
    filtro_empresa = st.selectbox("Empresa", empresas)

    status_opcoes = df["Status"].unique().tolist()
    filtro_status = st.multiselect(
        "Status", options=status_opcoes,
        default=status_opcoes,
        format_func=lambda x: LABEL_STATUS.get(x, x)
    )

# ── Aplicar filtros ───────────────────────────────────────────────────────────
dff = df.copy()
if filtro_usuario != "Todos":
    dff = dff[dff["Usuario_curto"] == filtro_usuario]
if filtro_empresa != "Todas":
    dff = dff[dff["Empresa_curta"] == filtro_empresa]
if filtro_status:
    dff = dff[dff["Status"].isin(filtro_status)]

total = len(dff)

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

s_fin  = int((dff["Status"] == "finalizada").sum())
s_atr  = int((dff["Status"] == "Finalizada em atraso").sum())
s_late = int((dff["Status"] == "atrasada").sum())
s_todo = int((dff["Status"] == "A fazer").sum())

k1.metric("✅ Finalizadas",      s_fin,  f"{s_fin/total*100:.0f}% do total"  if total else "—")
k2.metric("⏰ Em atraso",        s_atr,  f"{s_atr/total*100:.0f}% do total"  if total else "—")
k3.metric("🔴 Ainda atrasadas",  s_late, f"{s_late/total*100:.0f}% do total" if total else "—")
k4.metric("📌 A fazer",          s_todo, f"{s_todo/total*100:.0f}% do total" if total else "—")

# ── Linha 1: Distribuição + Evolução diária ───────────────────────────────────
st.markdown('<div class="section-title">Visão Geral</div>', unsafe_allow_html=True)
col_a, col_b = st.columns([1, 2])

with col_a:
    contagem = dff["Status"].value_counts().reset_index()
    contagem.columns = ["Status", "Qtd"]
    contagem["Label"] = contagem["Status"].map(LABEL_STATUS)
    fig_pizza = px.pie(
        contagem, values="Qtd", names="Label",
        color="Status",
        color_discrete_map={k: v for k, v in COR_STATUS.items()},
        hole=0.55,
    )
    fig_pizza.update_traces(textinfo="percent+label", showlegend=False)
    fig_pizza.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=260,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

with col_b:
    if "Data" in dff.columns:
        # Ordenar datas corretamente (dd/mm/yyyy)
        dff_d = dff.copy()
        try:
            dff_d["Data_dt"] = pd.to_datetime(dff_d["Data"], dayfirst=True, errors="coerce")
            daily = (
                dff_d.groupby(["Data_dt", "Status"])
                .size().reset_index(name="Qtd")
                .sort_values("Data_dt")
            )
            daily["Label"] = daily["Status"].map(LABEL_STATUS)
            fig_line = px.line(
                daily, x="Data_dt", y="Qtd", color="Status",
                color_discrete_map=COR_STATUS,
                labels={"Data_dt": "Data", "Qtd": "Tarefas", "Status": ""},
                markers=True,
            )
            fig_line.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.25),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig_line, use_container_width=True)
        except Exception:
            st.warning("Não foi possível plotar a evolução diária.")

# ── Linha 2: Por funcionário + Por empresa ────────────────────────────────────
st.markdown('<div class="section-title">Por Funcionário e Empresa</div>', unsafe_allow_html=True)
col_c, col_d = st.columns(2)

with col_c:
    user_data = (
        dff.groupby(["Usuario_curto", "Status"])
        .size().reset_index(name="Qtd")
    )
    user_data["Label"] = user_data["Status"].map(LABEL_STATUS)
    fig_user = px.bar(
        user_data, x="Qtd", y="Usuario_curto", color="Status",
        color_discrete_map=COR_STATUS,
        orientation="h", barmode="stack",
        labels={"Usuario_curto": "", "Qtd": "Tarefas", "Status": ""},
    )
    fig_user.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_user, use_container_width=True)

with col_d:
    emp_data = (
        dff.groupby(["Empresa_curta", "Status"])
        .size().reset_index(name="Qtd")
    )
    emp_total = emp_data.groupby("Empresa_curta")["Qtd"].sum().nlargest(10).index
    emp_data = emp_data[emp_data["Empresa_curta"].isin(emp_total)]

    fig_emp = px.bar(
        emp_data, x="Qtd", y="Empresa_curta", color="Status",
        color_discrete_map=COR_STATUS,
        orientation="h", barmode="stack",
        labels={"Empresa_curta": "", "Qtd": "Tarefas", "Status": ""},
    )
    fig_emp.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_emp, use_container_width=True)

# ── Linha 3: Tabela de eficiência por funcionário ─────────────────────────────
st.markdown('<div class="section-title">Eficiência por Funcionário</div>', unsafe_allow_html=True)

perf = dff.groupby(["Usuario_curto", "Status"]).size().unstack(fill_value=0).reset_index()
for col in ["finalizada", "Finalizada em atraso", "atrasada", "A fazer"]:
    if col not in perf.columns:
        perf[col] = 0

perf["Total"] = perf[["finalizada", "Finalizada em atraso", "atrasada", "A fazer"]].sum(axis=1)
perf["Eficiência"] = (perf["finalizada"] / perf["Total"]).where(perf["Total"] > 0, 0)

tabela = perf.rename(columns={
    "Usuario_curto":        "Funcionário",
    "finalizada":           "✅ Finalizada",
    "Finalizada em atraso": "⏰ Em atraso",
    "atrasada":             "🔴 Atrasada",
    "A fazer":              "📌 A fazer",
})[["Funcionário", "Total", "✅ Finalizada", "⏰ Em atraso", "🔴 Atrasada", "📌 A fazer", "Eficiência"]]

def cor_eficiencia(val):
    if val >= 0.6:
        return "background-color: #d5f5e3; color: #1a7a3c; font-weight: 600"
    elif val >= 0.4:
        return "background-color: #fdebd0; color: #a04000; font-weight: 600"
    else:
        return "background-color: #fadbd8; color: #922b21; font-weight: 600"

st.dataframe(
    tabela.style
          .format({"Eficiência": "{:.0%}"})
          .applymap(cor_eficiencia, subset=["Eficiência"]),
    use_container_width=True,
    hide_index=True,
)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Total de registros exibidos: **{total}** · Fonte: arquivo carregado na sidebar")
