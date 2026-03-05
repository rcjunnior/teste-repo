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

# ── Estilo ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.6rem !important; font-weight: 700 !important; }
    .section-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin: 1.4rem 0 0.5rem;
        border-bottom: 1px solid #444;
        padding-bottom: 4px;
    }
    .kpi-card {
        border-radius: 10px;
        padding: 16px 18px;
        border-left: 5px solid;
        margin-bottom: 4px;
    }
    .kpi-label {
        font-size: 0.7rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
    }
    .kpi-value { font-size: 2.2rem; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .kpi-sub   { font-size: 0.75rem; opacity: 0.7; }
    .emp-row {
        display: flex; align-items: center; padding: 7px 0;
        border-bottom: 1px solid rgba(128,128,128,0.15); gap: 10px;
    }
    .emp-name  { flex: 0 0 190px; font-size: 0.78rem; font-weight: 600; }
    .emp-bar-wrap {
        flex: 1; height: 10px; background: rgba(128,128,128,0.15);
        border-radius: 5px; overflow: hidden; display: flex;
    }
    .emp-count { flex: 0 0 36px; font-size: 0.78rem; text-align: right; opacity: 0.7; }
    .emp-pct   { flex: 0 0 44px; font-size: 0.72rem; text-align: right; opacity: 0.55; }
    .emp-alert { flex: 0 0 22px; font-size: 0.8rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
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

def kpi_card(label, value, sub, color, bg):
    return f"""
    <div class="kpi-card" style="background:{bg}; border-color:{color};">
        <div class="kpi-label" style="color:{color};">{label}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        <div class="kpi-sub"  style="color:{color};">{sub}</div>
    </div>"""

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def cor_eficiencia(val):
    if val >= 0.6:   return "background-color:#1a4a2e; color:#2ECC71; font-weight:600"
    elif val >= 0.4: return "background-color:#4a3010; color:#F39C12; font-weight:600"
    else:            return "background-color:#4a1010; color:#E74C3C; font-weight:600"

# ── Carregamento ──────────────────────────────────────────────────────────────
@st.cache_data
def carregar(arquivo):
    df = pd.read_excel(arquivo)
    df["Usuário"] = df["Usuário"].fillna("Sem usuário")
    df["Empresa"] = df["Empresa"].fillna("Sem empresa")
    df["Usuario_curto"] = df["Usuário"].apply(
        lambda x: " ".join(x.replace("Operador ", "").replace("Gestor ", "").split()[:2])
    )
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.title("📋 Painel de Tarefas")

with st.sidebar:
    st.header("Dados")
    arquivo = st.file_uploader("Carregar Excel (.xlsx)", type=["xlsx"])
    st.caption("Substitua o arquivo para atualizar o painel.")

if arquivo is None:
    st.info("⬅️ Faça upload do arquivo Excel na barra lateral para começar.")
    st.stop()

df = carregar(arquivo)

with st.sidebar:
    st.markdown("---")
    st.header("Filtros")
    usuarios = ["Todos"] + sorted(df["Usuario_curto"].unique().tolist())
    filtro_usuario = st.selectbox("Funcionário", usuarios)

    empresas_lista = sorted(df["Empresa"].unique().tolist())
    filtro_empresa = st.selectbox("Empresa", ["Todas"] + empresas_lista)

    status_opcoes = df["Status"].unique().tolist()
    filtro_status = st.multiselect(
        "Status", options=status_opcoes, default=status_opcoes,
        format_func=lambda x: LABEL_STATUS.get(x, x)
    )
    st.markdown("---")
    top_n = st.slider("Empresas no gráfico", min_value=5, max_value=len(empresas_lista), value=15, step=5)

# ── Filtros ───────────────────────────────────────────────────────────────────
dff = df.copy()
if filtro_usuario != "Todos":      dff = dff[dff["Usuario_curto"] == filtro_usuario]
if filtro_empresa != "Todas":      dff = dff[dff["Empresa"] == filtro_empresa]
if filtro_status:                  dff = dff[dff["Status"].isin(filtro_status)]
total = len(dff)

# ── KPIs ──────────────────────────────────────────────────────────────────────
s_fin  = int((dff["Status"] == "finalizada").sum())
s_atr  = int((dff["Status"] == "Finalizada em atraso").sum())
s_late = int((dff["Status"] == "atrasada").sum())
s_todo = int((dff["Status"] == "A fazer").sum())

k1, k2, k3, k4 = st.columns(4)
k1.markdown(kpi_card("✅ Finalizadas",     s_fin,  f"{s_fin/total*100:.0f}% do total"  if total else "—", "#2ECC71", "rgba(46,204,113,0.15)"),  unsafe_allow_html=True)
k2.markdown(kpi_card("⏰ Em atraso",       s_atr,  f"{s_atr/total*100:.0f}% do total"  if total else "—", "#E74C3C", "rgba(231,76,60,0.15)"),   unsafe_allow_html=True)
k3.markdown(kpi_card("🔴 Ainda atrasadas", s_late, f"{s_late/total*100:.0f}% do total" if total else "—", "#F39C12", "rgba(243,156,18,0.15)"),  unsafe_allow_html=True)
k4.markdown(kpi_card("📌 A fazer",         s_todo, f"{s_todo/total*100:.0f}% do total" if total else "—", "#3498DB", "rgba(52,152,219,0.15)"),  unsafe_allow_html=True)

# ── Visão Geral ───────────────────────────────────────────────────────────────
section("Visão Geral")
col_a, col_b = st.columns([1, 2])

with col_a:
    contagem = dff["Status"].value_counts().reset_index()
    contagem.columns = ["Status", "Qtd"]
    fig_pizza = px.pie(contagem, values="Qtd", names="Status",
        color="Status", color_discrete_map=COR_STATUS, hole=0.55)
    fig_pizza.update_traces(textinfo="percent+label", showlegend=False)
    fig_pizza.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=260,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pizza, use_container_width=True)

with col_b:
    try:
        dff_d = dff.copy()
        dff_d["Data_dt"] = pd.to_datetime(dff_d["Data"], dayfirst=True, errors="coerce")
        daily = (dff_d.groupby(["Data_dt","Status"]).size()
                 .reset_index(name="Qtd").sort_values("Data_dt"))
        fig_line = px.line(daily, x="Data_dt", y="Qtd", color="Status",
            color_discrete_map=COR_STATUS,
            labels={"Data_dt":"Data","Qtd":"Tarefas","Status":""}, markers=True)
        fig_line.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=260,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.25), xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"))
        st.plotly_chart(fig_line, use_container_width=True)
    except Exception:
        st.warning("Não foi possível plotar a evolução diária.")

# ── Por Funcionário ───────────────────────────────────────────────────────────
section("Por Funcionário")
col_c, col_d = st.columns([1, 1])

with col_c:
    user_data = dff.groupby(["Usuario_curto","Status"]).size().reset_index(name="Qtd")
    fig_user = px.bar(user_data, x="Qtd", y="Usuario_curto", color="Status",
        color_discrete_map=COR_STATUS, orientation="h", barmode="stack",
        labels={"Usuario_curto":"","Qtd":"Tarefas","Status":""})
    fig_user.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2), yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"))
    st.plotly_chart(fig_user, use_container_width=True)

with col_d:
    perf = dff.groupby(["Usuario_curto","Status"]).size().unstack(fill_value=0).reset_index()
    for c in ["finalizada","Finalizada em atraso","atrasada","A fazer"]:
        if c not in perf.columns: perf[c] = 0
    perf["Total"] = perf[["finalizada","Finalizada em atraso","atrasada","A fazer"]].sum(axis=1)
    perf["Eficiência"] = (perf["finalizada"] / perf["Total"]).where(perf["Total"] > 0, 0)
    tabela_perf = perf.rename(columns={
        "Usuario_curto":"Funcionário","finalizada":"✅ Finalizada",
        "Finalizada em atraso":"⏰ Em atraso","atrasada":"🔴 Atrasada","A fazer":"📌 A fazer",
    })[["Funcionário","Total","✅ Finalizada","⏰ Em atraso","🔴 Atrasada","📌 A fazer","Eficiência"]]
    st.dataframe(
        tabela_perf.style.format({"Eficiência":"{:.0%}"}).applymap(cor_eficiencia, subset=["Eficiência"]),
        use_container_width=True, hide_index=True,
    )

# ── Análise Detalhada por Empresa ─────────────────────────────────────────────
section("Análise Detalhada por Empresa")

emp_full = dff.groupby(["Empresa","Status"]).size().unstack(fill_value=0).reset_index()
for c in ["finalizada","Finalizada em atraso","atrasada","A fazer"]:
    if c not in emp_full.columns: emp_full[c] = 0
emp_full["Total"]      = emp_full[["finalizada","Finalizada em atraso","atrasada","A fazer"]].sum(axis=1)
emp_full["Pendentes"]  = emp_full["atrasada"] + emp_full["A fazer"]
emp_full["Eficiência"] = (emp_full["finalizada"] / emp_full["Total"]).where(emp_full["Total"] > 0, 0)
emp_full = emp_full.sort_values("Total", ascending=False)

tab1, tab2, tab3 = st.tabs(["📊 Gráfico", "🏆 Ranking completo", "📋 Tabela completa"])

with tab1:
    top_emp = emp_full.nlargest(top_n, "Total")
    emp_melt = top_emp.melt(
        id_vars="Empresa",
        value_vars=["finalizada","Finalizada em atraso","atrasada","A fazer"],
        var_name="Status", value_name="Qtd"
    )
    emp_melt["Empresa_curta"] = emp_melt["Empresa"].apply(lambda x: " ".join(x.split()[:3]))
    fig_emp = px.bar(emp_melt, x="Qtd", y="Empresa_curta", color="Status",
        color_discrete_map=COR_STATUS, orientation="h", barmode="stack",
        labels={"Empresa_curta":"","Qtd":"Tarefas","Status":""})
    fig_emp.update_layout(
        margin=dict(t=10,b=10,l=10,r=10),
        height=max(300, top_n * 30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.08),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
    )
    st.plotly_chart(fig_emp, use_container_width=True)

with tab2:
    st.caption(f"Todas as {len(emp_full)} empresas ordenadas por volume · 🔴 = possui tarefas pendentes ou atrasadas")
    max_total = int(emp_full["Total"].max())
    rows_html = ""
    for _, row in emp_full.iterrows():
        tot   = int(row["Total"])
        fin   = int(row["finalizada"])
        atr   = int(row["Finalizada em atraso"])
        late  = int(row["atrasada"])
        afaz  = int(row["A fazer"])
        pct   = tot / max_total * 100 if max_total else 0
        alert = "🔴" if (late + afaz) > 0 else "✅"
        seg_fin  = fin  / tot * 100 if tot else 0
        seg_atr  = atr  / tot * 100 if tot else 0
        seg_late = late / tot * 100 if tot else 0
        seg_afaz = afaz / tot * 100 if tot else 0
        nome = " ".join(row["Empresa"].split()[:4])
        rows_html += f"""
        <div class="emp-row">
            <div class="emp-alert">{alert}</div>
            <div class="emp-name" title="{row['Empresa']}">{nome}</div>
            <div class="emp-bar-wrap">
                <div style="width:{seg_fin:.1f}%;background:#2ECC71;height:100%"></div>
                <div style="width:{seg_atr:.1f}%;background:#E74C3C;height:100%"></div>
                <div style="width:{seg_late:.1f}%;background:#F39C12;height:100%"></div>
                <div style="width:{seg_afaz:.1f}%;background:#3498DB;height:100%"></div>
            </div>
            <div class="emp-count">{tot}</div>
            <div class="emp-pct">{pct:.0f}%</div>
        </div>"""
    st.markdown(rows_html, unsafe_allow_html=True)
    st.caption("Barra: 🟢 Finalizada · 🔴 Em atraso · 🟡 Atrasada · 🔵 A fazer · Coluna % = proporção em relação à empresa com maior volume")

with tab3:
    tabela_emp = emp_full.rename(columns={
        "finalizada":"✅ Finalizada","Finalizada em atraso":"⏰ Em atraso",
        "atrasada":"🔴 Atrasada","A fazer":"📌 A fazer",
        "Pendentes":"⚠️ Pendentes","Eficiência":"Eficiência",
    })[["Empresa","Total","✅ Finalizada","⏰ Em atraso","🔴 Atrasada","📌 A fazer","⚠️ Pendentes","Eficiência"]]
    st.dataframe(
        tabela_emp.style.format({"Eficiência":"{:.0%}"}).applymap(cor_eficiencia, subset=["Eficiência"]),
        use_container_width=True, hide_index=True,
    )
    csv_emp = tabela_emp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar tabela de empresas (CSV)", csv_emp, "empresas.csv", "text/csv")

# ── Exportar / Imprimir ───────────────────────────────────────────────────────
section("Exportar Relatório")

st.markdown("""
> **Como salvar o painel como PDF:**  
> Use o atalho nativo do navegador — preserva todos os gráficos e tabelas exatamente como estão na tela.
""")

col_p1, col_p2, col_p3 = st.columns(3)
col_p1.info("**Windows / Linux**\n\nCtrl + P → *Salvar como PDF*")
col_p2.info("**Mac**\n\nCmd + P → *Salvar como PDF*")
col_p3.info("**Dica de qualidade**\n\nOrientação **Paisagem** + margens **Mínimas**")

section("Download dos Dados Filtrados")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    csv_full = dff.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Dados filtrados (CSV)", csv_full,
        "tarefas_filtradas.csv", "text/csv", use_container_width=True)

with col_dl2:
    resumo = perf.copy()
    resumo["Eficiência"] = (resumo["Eficiência"] * 100).round(1).astype(str) + "%"
    resumo = resumo.rename(columns={"Usuario_curto":"Funcionário","finalizada":"Finalizada",
        "Finalizada em atraso":"Em atraso","atrasada":"Atrasada","A fazer":"A fazer"})
    csv_res = resumo[["Funcionário","Total","Finalizada","Em atraso","Atrasada","A fazer","Eficiência"]].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Resumo por funcionário (CSV)", csv_res,
        "resumo_funcionarios.csv", "text/csv", use_container_width=True)

st.markdown("---")
st.caption(f"Total de registros exibidos: **{total}** · Fonte: arquivo carregado na sidebar")
