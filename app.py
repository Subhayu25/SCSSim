# app.py
# TropiC+ — The Fresh Connection (Rounds 0–6) Dashboard
# Streamlit app with functional→financial KPI mapping and professional UI.

import io
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# -----------------------------
# Page config & styling
# -----------------------------
st.set_page_config(
    page_title="TropiC+ • The Fresh Connection (R0–R6)",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme accents (kept consistent with your Lovable dashboard) ---
PRIMARY = "#1F2340"  # deep navy
ACCENT  = "#FF7A00"  # orange
CARD_BG = "#FFFFFF"
SUBTLE  = "#F3F5F9"

CUSTOM_CSS = f"""
<style>
/* Clean, modern look */
section.main > div {{ padding-top: 1rem; }}
/* KPI cards */
.kpi-card {{
  background: {CARD_BG};
  border: 1px solid #E8ECF3;
  border-radius: 14px;
  padding: 18px 18px 12px 18px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
}}
.kpi-title {{
  color: #6B7280; font-size: 0.8rem; text-transform: uppercase; letter-spacing: .06rem;
}}
.kpi-value {{
  font-size: 1.8rem; font-weight: 700; color: {PRIMARY};
}}
.kpi-sub {{
  color: #6B7280; font-size: 0.85rem;
}}
/* Footer */
.footer {{
  margin-top: 48px; padding: 16px 0; border-top: 1px solid #eaecef; color:#4B5563;
}}
/* Section header watermark look */
.section-head {{
  position: relative;
  padding: 12px 16px;
  background: {SUBTLE};
  border-radius: 12px;
  border: 1px solid #E8ECF3;
}}
.section-head h3 {{
  margin: 0; color: {PRIMARY};
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------
@st.cache_data(show_spinner=False)
def load_excel(path: str) -> dict:
    """Load all relevant sheets, return dict of normalized DataFrames."""
    xl = pd.ExcelFile(path)
    def norm(df):
        df2 = df.copy()
        df2.columns = (
            df2.columns
            .str.strip()
            .str.lower()
            .str.replace("\n"," ", regex=False)
            .str.replace("\r"," ", regex=False)
            .str.replace("  "," ", regex=False)
            .str.replace(" ","_", regex=False)
        )
        return df2

    def get_sheet(name):
        if name in xl.sheet_names:
            return norm(pd.read_excel(xl, sheet_name=name))
        return None

    df_product   = get_sheet("Product")
    df_component = get_sheet("Component")
    df_wh        = get_sheet("Warehouse, Salesarea")
    # Optional sheets (won't break if absent)
    df_customer  = get_sheet("Customer")
    df_prod_wh   = get_sheet("Product - Warehouse")

    return {
        "product": df_product,
        "component": df_component,
        "warehouse": df_wh,
        "customer": df_customer,
        "product_warehouse": df_prod_wh,
    }

def pct(x, decimals=2):
    if pd.isna(x): return None
    return round(float(x)*100.0, decimals)

def num(x, decimals=2):
    if pd.isna(x): return None
    return round(float(x), decimals)

def layout_kpi(title, value, sub=None, suffix=""):
    v = "-" if value is None else f"{value}{suffix}"
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{v}</div>
          <div class="kpi-sub">{sub or ""}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def line_chart(df, x, y, title=None, yaxis_title=None, color=None, secondary_y=None):
    fig = go.Figure()
    if isinstance(y, list):
        for col in y:
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col))
    else:
        fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines+markers", name=y))

    if secondary_y and isinstance(secondary_y, list):
        for col in secondary_y:
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col, yaxis="y2"))

        fig.update_layout(
            yaxis=dict(title=yaxis_title or ""),
            yaxis2=dict(title="", overlaying='y', side='right', showgrid=False),
        )
    else:
        fig.update_layout(yaxis=dict(title=yaxis_title or ""))

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        title=title or "",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        template="plotly_white",
    )
    return fig

def bar_line_combo(df, x, bar_y, line_y, title=None, y1_title="", y2_title=""):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df[x], y=df[bar_y], name=bar_y, marker_color=ACCENT))
    fig.add_trace(go.Scatter(x=df[x], y=df[line_y], name=line_y, yaxis="y2", mode="lines+markers"))

    fig.update_layout(
        title=title or "",
        xaxis=dict(title=x),
        yaxis=dict(title=y1_title),
        yaxis2=dict(title=y2_title, overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        template="plotly_white",
        barmode="group",
    )
    return fig

# -----------------------------
# Data prep (using your real Excel)
# -----------------------------
DATA_PATH = "TFC_0_6.xlsx"     # Upload to repo root
LOGO_PATH = "logo_tfc.png"     # Upload to repo root

dfs = load_excel(DATA_PATH)
prod = dfs["product"]
comp = dfs["component"]
wh   = dfs["warehouse"]

if prod is None or comp is None or wh is None:
    st.error("Required sheets not found. Please make sure `TFC_0_6.xlsx` has sheets: Product, Component, Warehouse, Salesarea.")
    st.stop()

# Product aggregates by round
prod_agg = prod.groupby("round").agg(
    avg_service_pct=("service_level_(pieces)", "mean"),
    fg_stock_weeks_avg=("stock_(weeks)", "mean"),
    mape_pct=("forecast_error_(mape)", "mean"),
    product_obsol_pct_avg=("obsoletes_(%)","mean"),
    realized_revenue=("demand_per_week_(value)","sum"),
    gross_margin_per_week=("gross_margin_per_week","sum"),
).reset_index()

# Financials
prod_agg["cogs"] = prod_agg["realized_revenue"] - prod_agg["gross_margin_per_week"]

# Component aggregates
comp_agg = comp.groupby("round").agg(
    component_availability_pct_avg=("component_availability_(%)","mean"),
    component_stock_weeks_avg=("stock_(weeks)","mean"),
    component_obsolescence_pct_avg=("obsoletes_(%)","mean"),
    component_delivery_reliability_pct_avg=("delivery_reliability_(%)","mean"),
).reset_index()

# Vitamin C obsolescence by round
vitc = comp[comp["component"].str.contains("vitamin", case=False, na=False)]
vitc_obsol = vitc.groupby("round")["obsoletes_(%)"].mean().reset_index()

# Component pivots
weeks_pivot = comp.pivot_table(index="round", columns="component", values="stock_(weeks)", aggfunc="mean").reset_index()
avail_pivot = comp.pivot_table(index="round", columns="component", values="component_availability_(%)", aggfunc="mean").reset_index()

# Warehouse/Operations
inbound = wh[wh["warehouse"].str.contains("raw materials", case=False, na=False)] \
            .groupby("round")["cube_utilization_(%)"].mean().reset_index().rename(columns={"cube_utilization_(%)":"inbound_util"})
outbound = wh[wh["warehouse"].str.contains("finished goods", case=False, na=False)] \
            .groupby("round")["cube_utilization_(%)"].mean().reset_index().rename(columns={"cube_utilization_(%)":"outbound_util"})
ppa = prod.groupby("round")["production_plan_adherence_(%)"].mean().reset_index().rename(columns={"production_plan_adherence_(%)":"ppa"})

# Join common round index
rounds_df = pd.DataFrame({"round": sorted(prod_agg["round"].unique())})
overview = (
    rounds_df
    .merge(prod_agg, on="round", how="left")
    .merge(comp_agg, on="round", how="left")
    .merge(inbound, on="round", how="left")
    .merge(outbound, on="round", how="left")
    .merge(ppa, on="round", how="left")
)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.image(LOGO_PATH, caption="The Fresh Connection", use_column_width=True)
st.sidebar.markdown("### Filters")
min_r, max_r = int(overview["round"].min()), int(overview["round"].max())
sel = st.sidebar.slider("Round range", min_value=min_r, max_value=max_r, value=(min_r, max_r), step=1)
mask = (overview["round"] >= sel[0]) & (overview["round"] <= sel[1])
ov = overview[mask].copy()

latest = int(ov["round"].max())
ov_latest = ov[ov["round"]==latest].iloc[0].to_dict()

# -----------------------------
# Header
# -----------------------------
col_logo, col_title = st.columns([1,6])
with col_logo:
    st.image(LOGO_PATH, width=90)
with col_title:
    st.markdown(f"## **TropiC+ Command Center — The Fresh Connection (Rounds {sel[0]}–{sel[1]})**")
    st.caption("Performance Insights, Functional→Financial KPI Links, and Next-Round Focus")

# -----------------------------
# KPI Cards (latest round)
# -----------------------------
c1, c2, c3, c4, c5 = st.columns(5)
with c1: layout_kpi("Avg Product Service Level", pct(ov_latest["avg_service_pct"]), suffix="%")
with c2: layout_kpi("Component Availability", pct(ov_latest["component_availability_pct_avg"]), suffix="%")
with c3: layout_kpi("FG Stock Weeks", num(ov_latest["fg_stock_weeks_avg"]))
with c4: layout_kpi("Production Plan Adherence", pct(ov_latest["ppa"]), suffix="%")
with c5: layout_kpi("Gross Margin / wk", num(ov_latest["gross_margin_per_week"]))

st.markdown("<div class='section-head'><h3>Overview</h3></div>", unsafe_allow_html=True)
oc1, oc2 = st.columns(2)
with oc1:
    st.plotly_chart(
        line_chart(ov, "round",
                   ["avg_service_pct","component_availability_pct_avg","ppa"],
                   title="Service, Availability & Plan Adherence (%, by Round)",
                   yaxis_title="%"),
        use_container_width=True)
with oc2:
    st.plotly_chart(
        bar_line_combo(ov, "round", "realized_revenue", "cogs",
                       title="Financials: Revenue (bars) vs COGS (line)",
                       y1_title="Revenue", y2_title="COGS"),
        use_container_width=True)

oc3, oc4 = st.columns(2)
with oc3:
    st.plotly_chart(
        line_chart(ov, "round", ["fg_stock_weeks_avg"], title="FG Stock Weeks (Avg)", yaxis_title="Weeks"),
        use_container_width=True)
with oc4:
    st.plotly_chart(
        line_chart(ov, "round", ["mape_pct","product_obsol_pct_avg"], title="MAPE & FG Obsolescence (%, by Round)", yaxis_title="%"),
        use_container_width=True)

# -----------------------------
# Purchase
# -----------------------------
st.markdown("<div class='section-head'><h3>Purchase</h3></div>", unsafe_allow_html=True)
st.write(
    "- Suppliers unchanged; lot sizes unchanged.\n"
    "- Increased delivery windows to improve delivery reliability.\n"
    "- Trade-off: reliability ↑, flexibility ↓; Vitamin C overstock risk."
)
pc1, pc2 = st.columns(2)
with pc1:
    st.plotly_chart(
        line_chart(ov, "round",
                   ["component_delivery_reliability_pct_avg","component_availability_pct_avg"],
                   title="Delivery Reliability vs Component Availability (%, by Round)",
                   yaxis_title="%"),
        use_container_width=True)
with pc2:
    st.plotly_chart(
        line_chart(ov, "round",
                   ["component_obsolescence_pct_avg","component_stock_weeks_avg"],
                   title="Component Obsolescence % vs Stock Weeks (by Round)",
                   yaxis_title="Value"),
        use_container_width=True)

# Component small multiples (weeks + availability)
st.markdown("**Component Inventory & Availability by Round**")
if not weeks_pivot.empty:
    comp_list = [c for c in weeks_pivot.columns if c != "round"]
    cc1, cc2 = st.columns(2)
    with cc1:
        tabs = st.tabs([f"Stock Weeks — {c}" for c in comp_list[:3]])
        for i, c in enumerate(comp_list[:3]):
            with tabs[i]:
                fig = line_chart(weeks_pivot, "round", [c], title=f"{c} — Weeks of Stock", yaxis_title="Weeks")
                st.plotly_chart(fig, use_container_width=True)
    with cc2:
        tabs2 = st.tabs([f"Availability — {c}" for c in comp_list[:3]])
        for i, c in enumerate(comp_list[:3]):
            with tabs2[i]:
                fig = line_chart(avail_pivot, "round", [c], title=f"{c} — Availability %", yaxis_title="%")
                st.plotly_chart(fig, use_container_width=True)

# Vitamin C obsolescence callout
if not vitc_obsol.empty:
    fig_vc = line_chart(vitc_obsol, "round", ["obsoletes_(%)"], title="Vitamin C Obsolescence (%)", yaxis_title="%")
    st.plotly_chart(fig_vc, use_container_width=True)

# -----------------------------
# Sales
# -----------------------------
st.markdown("<div class='section-head'><h3>Sales</h3></div>", unsafe_allow_html=True)
st.write(
    "- Focused on Food & Grocery to protect profitability.\n"
    "- Reduced service to Land Market & Dominics when needed.\n"
    "- Goal: meet SLAs while managing forecast error."
)
sc1, sc2 = st.columns(2)
with sc1:
    st.plotly_chart(
        line_chart(ov, "round", ["avg_service_pct"], title="Average Service Level (%, by Round)", yaxis_title="%"),
        use_container_width=True)
with sc2:
    st.plotly_chart(
        line_chart(ov, "round", ["mape_pct"], title="Forecast Error (MAPE %, by Round)", yaxis_title="%"),
        use_container_width=True)

st.plotly_chart(
    bar_line_combo(ov, "round", "realized_revenue", "product_obsol_pct_avg",
                   title="Revenue (bars) vs FG Obsolescence % (line)", y1_title="Revenue", y2_title="Obsolescence %"),
    use_container_width=True)

# -----------------------------
# Supply Chain
# -----------------------------
st.markdown("<div class='section-head'><h3>Supply Chain</h3></div>", unsafe_allow_html=True)
st.plotly_chart(
    line_chart(ov, "round", ["component_availability_pct_avg"], title="Component Availability (%, by Round)", yaxis_title="%"),
    use_container_width=True)
st.plotly_chart(
    line_chart(ov, "round", ["fg_stock_weeks_avg"], title="FG Stock Weeks (by Round)", yaxis_title="Weeks"),
    use_container_width=True)

# -----------------------------
# Operations
# -----------------------------
st.markdown("<div class='section-head'><h3>Operations</h3></div>", unsafe_allow_html=True)
oc1, oc2, oc3 = st.columns(3)
with oc1: layout_kpi("Inbound Cube Utilization", pct(ov_latest.get("inbound_util")), "Target 85–90%", suffix="%")
with oc2: layout_kpi("Outbound Cube Utilization", pct(ov_latest.get("outbound_util")), "Target 85–90%", suffix="%")
with oc3: layout_kpi("Plan Adherence", pct(ov_latest.get("ppa")), "Higher is better", suffix="%")

st.plotly_chart(
    line_chart(ov, "round", ["inbound_util","outbound_util"], title="Cube Utilization (%, by Round)", yaxis_title="%"),
    use_container_width=True)
st.plotly_chart(
    line_chart(ov, "round", ["ppa"], title="Production Plan Adherence (%, by Round)", yaxis_title="%"),
    use_container_width=True)

# -----------------------------
# Impact Matrix (Functional → Financial)
# -----------------------------
st.markdown("<div class='section-head'><h3>Impact Matrix — Functional KPIs ↔ Financial KPIs</h3></div>",
            unsafe_allow_html=True)

im1, im2 = st.columns(2)
with im1:
    fig = line_chart(ov, "round",
                     ["component_delivery_reliability_pct_avg", "component_availability_pct_avg"],
                     title="Purchase → Reliability & Availability (proxy for COGS risk)", yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Higher reliability supports availability and reduces stockout/expedite risk; excessive component stock increases handling/COGS.")

with im2:
    fig = bar_line_combo(ov, "round", "realized_revenue", "avg_service_pct",
                         title="Sales → Service Level (line) vs Revenue (bars)", y1_title="Revenue", y2_title="Service %")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Service protects realized revenue; service dips correlate with revenue softness.")

im3, im4 = st.columns(2)
with im3:
    fig = line_chart(ov, "round", ["component_availability_pct_avg", "realized_revenue"],
                     title="Supply Chain → Availability vs Revenue", yaxis_title="", secondary_y=["realized_revenue"])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Availability >95% preserves revenue; risk managed using safety stocks.")

with im4:
    fig = line_chart(ov, "round", ["outbound_util", "ppa"],
                     title="Operations → Utilization vs Plan Adherence (cost drivers)", yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Utilization near 85–90% controls indirect costs; low adherence can raise COGS through expediting/rework.")

# -----------------------------
# Data Explorer
# -----------------------------
st.markdown("<div class='section-head'><h3>Data Explorer</h3></div>", unsafe_allow_html=True)

with st.expander("Per-round KPI Table"):
    show_cols = [
        "round","avg_service_pct","component_availability_pct_avg","fg_stock_weeks_avg",
        "mape_pct","product_obsol_pct_avg","realized_revenue","cogs","gross_margin_per_week",
        "inbound_util","outbound_util","ppa"
    ]
    tidy = ov[show_cols].copy()
    # scale percents nicely for display
    pct_cols = ["avg_service_pct","component_availability_pct_avg","mape_pct","product_obsol_pct_avg",
                "inbound_util","outbound_util","ppa"]
    for c in pct_cols:
        tidy[c] = (tidy[c]*100).round(2)
    st.dataframe(tidy, use_container_width=True)
    st.download_button("Download CSV", data=tidy.to_csv(index=False), file_name="tropic_kpis_rounds.csv", mime="text/csv")

# -----------------------------
# Footer
# -----------------------------
st.markdown(
    """
    <div class="footer">
      <div><strong>Supply Chain Simulation Final Presentation</strong></div>
      <div><em>Team TropiC+: Dhruvi Damani, Ranveer Lal, Saraj Tanwar & Subhayu Bhattacharya</em></div>
    </div>
    """,
    unsafe_allow_html=True
)
