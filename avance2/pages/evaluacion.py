import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="Dashboard Educativo", page_icon="📊", layout="wide")

# -----------------------------
# CSS (sidebar + ajustes suaves)
# -----------------------------


# -----------------------------
# Rutas robustas (funciona aunque estés en pages/)
# -----------------------------
THIS_FILE = Path(__file__).resolve()
THIS_DIR = THIS_FILE.parent

# Si estás dentro de .../avance2/pages/, entonces APP_DIR = .../avance2
APP_DIR = THIS_DIR.parent if THIS_DIR.name == "pages" else THIS_DIR

def find_first_existing(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None

# CSV: búscalo en lugares comunes
CSV_CANDIDATES = [
    APP_DIR / "dataset_educativo_1000_realista_puntoycoma.csv",
    THIS_DIR / "dataset_educativo_1000_realista_puntoycoma.csv",
]

# Logo: búscalo en lugares comunes
LOGO_CANDIDATES = [
    APP_DIR / "imagen" / "logo.png",
    THIS_DIR / "imagen" / "logo.png",
]

CSV_PATH = find_first_existing(CSV_CANDIDATES)
LOGO_PATH = find_first_existing(LOGO_CANDIDATES)

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data
def cargar_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")

def multiselect_todos(label, serie):
    opciones = list(pd.Series(serie).dropna().unique())
    return st.sidebar.multiselect(label, options=opciones, default=opciones)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">📁 Fuente de datos</div>', unsafe_allow_html=True)

modo = st.sidebar.radio("¿Cómo cargar datos?", ["Usar CSV local", "Subir CSV"], horizontal=False)

if modo == "Subir CSV":
    up = st.sidebar.file_uploader("Sube el CSV (preferible con ; )", type=["csv"])
    if up is None:
        st.warning("Sube un archivo CSV para continuar.")
        st.stop()
    df = pd.read_csv(up, sep=";", encoding="utf-8-sig")
else:
    if CSV_PATH is None:
        st.error(
            "No encontré el CSV local.\n\n"
            "✅ Ponlo en:\n"
            f"- {APP_DIR}\\dataset_educativo_1000_realista_puntoycoma.csv  (recomendado)\n"
            "o en la misma carpeta del script."
        )
        st.stop()
    df = cargar_csv(CSV_PATH)

# -----------------------------
# Limpieza básica
# -----------------------------
df = df.dropna().copy()
mes_orden = ["Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov"]
if "Mes" in df.columns:
    df["Mes"] = pd.Categorical(df["Mes"], categories=mes_orden, ordered=True)

# -----------------------------
# Filtros
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-title">🎛️ Filtros</div>', unsafe_allow_html=True)

f_periodo = multiselect_todos("Periodo", df["Periodo"])
f_sede    = multiselect_todos("Sede", df["Sede"])
f_turno   = multiselect_todos("Turno", df["Turno"])
f_grado   = multiselect_todos("Grado", df["Grado"])
f_curso   = multiselect_todos("Curso", df["Curso"])
f_mes     = multiselect_todos("Mes", df["Mes"]) if "Mes" in df.columns else list(df.index)

df_f = df[
    df["Periodo"].isin(f_periodo) &
    df["Sede"].isin(f_sede) &
    df["Turno"].isin(f_turno) &
    df["Grado"].isin(f_grado) &
    df["Curso"].isin(f_curso) &
    (df["Mes"].isin(f_mes) if "Mes" in df.columns else True)
].copy()

if df_f.empty:
    st.warning("Con esos filtros no hay datos. Prueba ampliando opciones.")
    st.stop()

# -----------------------------
# Header
# -----------------------------
st.markdown("##  Dashboard Educativo")
st.caption("Inscripciones, asistencia y resultados .")

# -----------------------------
# KPIs (NORMAL con st.metric)
# -----------------------------
total_insc = int(df_f["Inscripciones"].sum())
total_apr  = int(df_f["Aprobados"].sum())
total_des  = int(df_f["Desaprobados"].sum())
retiros    = int(df_f["Retiros"].sum())
avg_asist  = float(df_f["Asistencia_Promedio_%"].mean())
avg_nota   = float(df_f["Promedio_Final"].mean())
tasa_apr   = (total_apr / total_insc * 100) if total_insc else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("📝 Inscripciones", f"{total_insc:,}".replace(",", " "))
c2.metric("✅ % Aprobación", f"{tasa_apr:.1f}%")
c3.metric("📶 Asistencia prom.", f"{avg_asist:.1f}%")
c4.metric("🎓 Nota promedio", f"{avg_nota:.2f}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("🟩 Aprobados", f"{total_apr:,}".replace(",", " "))
c6.metric("🟥 Desaprobados", f"{total_des:,}".replace(",", " "))
c7.metric("↩️ Retiros", f"{retiros:,}".replace(",", " "))
c8.metric("🏫 Sedes activas", f"{df_f['Sede'].nunique()}")

st.markdown("---")

# -----------------------------
# Gráficos (los tuyos)
# -----------------------------
left, right = st.columns(2)

curso_insc = (df_f.groupby("Curso", as_index=False)["Inscripciones"].sum()
              .sort_values("Inscripciones", ascending=False))
fig1 = px.bar(curso_insc, x="Curso", y="Inscripciones", title="Inscripciones por Curso")
left.plotly_chart(fig1, use_container_width=True)

sede_res = (df_f.groupby("Sede", as_index=False)[["Aprobados", "Desaprobados"]].sum())
sede_res_m = sede_res.melt(id_vars="Sede", var_name="Resultado", value_name="Total")
fig2 = px.bar(sede_res_m, x="Sede", y="Total", color="Resultado",
              barmode="stack", title="Aprobados vs Desaprobados por Sede")
right.plotly_chart(fig2, use_container_width=True)

left2, right2 = st.columns(2)

mes_asist = (df_f.groupby("Mes", as_index=False)["Asistencia_Promedio_%"].mean()
             .sort_values("Mes"))
fig3 = px.line(mes_asist, x="Mes", y="Asistencia_Promedio_%", markers=True,
               title="Asistencia Promedio por Mes")
left2.plotly_chart(fig3, use_container_width=True)

fig4 = px.scatter(df_f, x="Asistencia_Promedio_%", y="Promedio_Final",
                  color="Curso", hover_data=["Sede", "Turno", "Grado", "Seccion_ID"],
                  title="Relación: Asistencia vs Nota Final")
right2.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# =========================================================
# NUEVOS GRÁFICOS
# =========================================================

# 1) Heatmap: % aprobación por Sede y Curso
st.subheader(" Aprobación por Sede y Curso")
tmp = df_f.groupby(["Sede", "Curso"], as_index=False)[["Inscripciones", "Aprobados"]].sum()
tmp["Tasa_Aprobacion_%"] = (tmp["Aprobados"] / tmp["Inscripciones"] * 100).round(1)
heat = tmp.pivot(index="Sede", columns="Curso", values="Tasa_Aprobacion_%")

try:
    fig_hm = px.imshow(heat, text_auto=True, aspect="auto", title="% Aprobación (Sede × Curso)")
    st.plotly_chart(fig_hm, use_container_width=True)
except Exception:
    st.info("Tu versión de plotly no soporta px.imshow. Mostrando tabla heatmap.")
    st.dataframe(heat, use_container_width=True)

colA, colB = st.columns(2)

with colA:
    st.subheader(" Notas por Curso")
    fig_box = px.box(df_f, x="Curso", y="Promedio_Final", points="outliers",
                     title="Distribución de Promedio Final por Curso")
    st.plotly_chart(fig_box, use_container_width=True)

with colB:
    st.subheader("  Distribución de Notas")
    fig_hist = px.histogram(df_f, x="Promedio_Final", nbins=20,
                            title="Distribución de Promedio Final")
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

colC, colD = st.columns(2)

with colC:
    st.subheader("Inscripciones por Sede / Grado / Curso")
    tree = df_f.groupby(["Sede", "Grado", "Curso"], as_index=False)["Inscripciones"].sum()
    fig_tree = px.treemap(tree, path=["Sede", "Grado", "Curso"], values="Inscripciones",
                          title="Mapa de tamaño: Inscripciones")
    st.plotly_chart(fig_tree, use_container_width=True)

with colD:
    st.subheader(" Embudo Académico")
    funnel_df = pd.DataFrame({
        "Etapa": ["Inscripciones", "Aprobados", "Desaprobados", "Retiros"],
        "Total": [total_insc, total_apr, total_des, retiros]
    })
    fig_funnel = px.funnel(funnel_df, x="Total", y="Etapa", title="Embudo Académico")
    st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")


# 8) Turno × Grado
st.subheader(" Turno × Grado: Asistencia Promedio")
tg = df_f.groupby(["Turno", "Grado"], as_index=False)["Asistencia_Promedio_%"].mean()
tg_p = tg.pivot(index="Turno", columns="Grado", values="Asistencia_Promedio_%")

try:
    fig_tg = px.imshow(tg_p, text_auto=True, aspect="auto",
                       title="Asistencia promedio (Turno × Grado)")
    st.plotly_chart(fig_tg, use_container_width=True)
except Exception:
    st.info("Tu versión de plotly no soporta px.imshow. Mostrando tabla Turno×Grado.")
    st.dataframe(tg_p, use_container_width=True)

st.markdown("---")

# -----------------------------
# Tabla + descarga
# -----------------------------
st.subheader("Datos filtrados")
st.dataframe(df_f, use_container_width=True, height=360)

csv_export = df_f.to_csv(index=False, sep=";", encoding="utf-8-sig")
st.download_button(
    "⬇️ Descargar datos filtrados (CSV)",
    data=csv_export,
    file_name="datos_filtrados.csv",
    mime="text/csv"
)
