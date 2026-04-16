import os
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None



warnings.filterwarnings("ignore")

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="VampireVolt",
    page_icon="⚡",
    layout="wide"
)

# =========================================================
# LOAD ENV + API
# =========================================================
load_dotenv()

try:
    api_key = st.secrets["API_KEY"]
except Exception:
    api_key = os.getenv("API_KEY")

client = Groq(api_key=api_key) if (api_key and Groq is not None) else None

# =========================================================
# THEME STATE
# =========================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "insights" not in st.session_state:
    st.session_state.insights = ""

# =========================================================
# THEME HELPERS
# =========================================================
def get_theme_colors():
    if st.session_state.theme == "dark":
        return {
            "bg": "#0d1117",
            "card": "#161b22",
            "sidebar": "#161b22",
            "text": "#e6edf3",
            "subtext": "#8b949e",
            "border": "#30363d",
            "banner1": "#132033",
            "banner2": "#1c2128",
            "plot_paper": "#0d1117",
            "plot_bg": "#161b22",
            "good": "#3fb950",
            "warn": "#d29922",
            "bad": "#f85149",
            "blue": "#388bfd",
            "blue2": "#79c0ff",
            "soft": "rgba(255,255,255,0.05)"
        }
    return {
        "bg": "#f5f7fa",
        "card": "#ffffff",
        "sidebar": "#ffffff",
        "text": "#111827",
        "subtext": "#4b5563",
        "border": "#d1d5db",
        "banner1": "#e0f2fe",
        "banner2": "#ffffff",
        "plot_paper": "#ffffff",
        "plot_bg": "#f5f7fa",
        "good": "#16a34a",
        "warn": "#ca8a04",
        "bad": "#dc2626",
        "blue": "#2563eb",
        "blue2": "#60a5fa",
        "soft": "rgba(0,0,0,0.03)"
    }

COLORS_DARK = [
    "#388bfd", "#3fb950", "#d29922", "#f85149", "#79c0ff",
    "#56d364", "#e3b341", "#ff7b72", "#a5d6ff", "#7ee787"
]

COLORS_LIGHT = [
    "#2563eb", "#16a34a", "#ca8a04", "#dc2626",
    "#60a5fa", "#4ade80", "#facc15", "#f87171"
]

def get_colors():
    return COLORS_DARK if st.session_state.theme == "dark" else COLORS_LIGHT

def get_layout():
    c = get_theme_colors()
    return dict(
        paper_bgcolor=c["plot_paper"],
        plot_bgcolor=c["plot_bg"],
        font=dict(color=c["text"], family="Segoe UI"),
    )

def apply_custom_css():
    c = get_theme_colors()

    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            background-color: {c["bg"]};
            color: {c["text"]};
            font-family: 'Segoe UI', sans-serif;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {c["sidebar"]} !important;
            border-right: 1px solid {c["border"]};
        }}

        section[data-testid="stSidebar"] * {{
            color: {c["text"]} !important;
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 1rem;
        }}

        .kpi-card {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            min-height: 120px;
        }}

        .kpi-label {{
            font-size: 11px;
            color: {c["subtext"]};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .kpi-value {{
            font-size: 28px;
            font-weight: 700;
            color: {c["text"]};
            line-height: 1.1;
        }}

        .kpi-sub {{
            font-size: 12px;
            margin-top: 8px;
        }}

        .good {{ color: {c["good"]}; }}
        .bad {{ color: {c["bad"]}; }}
        .neutral {{ color: {c["warn"]}; }}

        .banner {{
            background: linear-gradient(90deg, {c["banner1"]} 0%, {c["banner2"]} 100%);
            border: 1px solid {c["border"]};
            border-radius: 16px;
            padding: 22px;
            margin-bottom: 20px;
        }}

        .banner-title {{
            font-size: 28px;
            font-weight: 700;
            color: {c["text"]};
            margin-bottom: 6px;
        }}

        .banner-sub {{
            font-size: 14px;
            color: {c["subtext"]};
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: {c["text"]};
            margin-top: 10px;
            margin-bottom: 12px;
            border-bottom: 2px solid {c["border"]};
            padding-bottom: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# HELPERS
# =========================================================
def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def kpi_card(label, value, sub="", css_class="neutral"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub {css_class}">{sub}</div>
    </div>
    """

def rupees(x):
    return f"₹{x:,.2f}"

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    required_files = [
        "FactEnergyConsumption.csv",
        "DimAppliance.csv",
        "DimDate.csv",
        "DimHomeProfile.csv"
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(
            "Missing files: " + ", ".join(missing) +
            ". Keep all CSV files in the same folder as app.py"
        )

    fact = pd.read_csv("FactEnergyConsumption.csv")
    dim_appliance = pd.read_csv("DimAppliance.csv")
    dim_date = pd.read_csv("DimDate.csv")
    dim_home = pd.read_csv("DimHomeProfile.csv")

    fact.columns = [c.strip() for c in fact.columns]
    dim_appliance.columns = [c.strip() for c in dim_appliance.columns]
    dim_date.columns = [c.strip() for c in dim_date.columns]
    dim_home.columns = [c.strip() for c in dim_home.columns]

    if "Voltage" in fact.columns and "Volts" not in fact.columns:
        fact = fact.rename(columns={"Voltage": "Volts"})
    if "Current" in fact.columns and "Amps" not in fact.columns:
        fact = fact.rename(columns={"Current": "Amps"})

    if "Reading_Key" not in fact.columns:
        fact["Reading_Key"] = np.arange(1, len(fact) + 1)

    fact["Timestamp"] = pd.to_datetime(fact["Timestamp"], errors="coerce")

    if "Timestamp" in dim_date.columns:
        dim_date["Timestamp"] = pd.to_datetime(dim_date["Timestamp"], errors="coerce")

    if "Date" in dim_date.columns:
        dim_date["Date"] = pd.to_datetime(dim_date["Date"], errors="coerce")

    if "Timestamp" in dim_date.columns:
        df = (
            fact.merge(dim_appliance, on="Device_ID", how="left")
                .merge(dim_home, on="Home_ID", how="left")
                .merge(dim_date, on="Timestamp", how="left")
        )
    else:
        fact["Date"] = fact["Timestamp"].dt.floor("D")
        df = (
            fact.merge(dim_appliance, on="Device_ID", how="left")
                .merge(dim_home, on="Home_ID", how="left")
                .merge(dim_date, on="Date", how="left")
        )

    for col in ["Watts", "Volts", "Amps"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    if "Standby_Threshold_Watts" in df.columns:
        df["Standby_Threshold_Watts"] = pd.to_numeric(
            df["Standby_Threshold_Watts"], errors="coerce"
        ).fillna(10)
    else:
        df["Standby_Threshold_Watts"] = 10

    if "Date" not in df.columns or df["Date"].isna().all():
        df["Date"] = df["Timestamp"].dt.floor("D")

    if "Hour" not in df.columns:
        df["Hour"] = df["Timestamp"].dt.hour

    if "Minute" not in df.columns:
        df["Minute"] = df["Timestamp"].dt.minute

    if "Day_Name" not in df.columns:
        df["Day_Name"] = df["Timestamp"].dt.day_name()

    if "Day_Type" not in df.columns:
        df["Day_Type"] = np.where(df["Timestamp"].dt.weekday >= 5, "Weekend", "Weekday")

    if "Time_of_Day" not in df.columns:
        conditions = [
            df["Hour"].between(5, 11),
            df["Hour"].between(12, 16),
            df["Hour"].between(17, 20),
            df["Hour"].between(21, 23) | df["Hour"].between(0, 4)
        ]
        choices = ["Morning", "Afternoon", "Evening", "Night"]
        df["Time_of_Day"] = np.select(conditions, choices, default="Night")

    if "Device_Name" not in df.columns:
        df["Device_Name"] = df["Device_ID"].astype(str)

    if "Category" not in df.columns:
        df["Category"] = "Unknown"

    if "Is_Vampire_Source" not in df.columns:
        df["Is_Vampire_Source"] = False

    df["Home_ID"] = df["Home_ID"].astype(str)

    df["Energy_kWh"] = df["Watts"] / 1000 / 60
    df["Is_Standby"] = df["Watts"] <= df["Standby_Threshold_Watts"]
    df["Vampire_Watts"] = np.where(df["Is_Standby"], df["Watts"], 0)
    df["Active_Watts"] = np.where(df["Is_Standby"], 0, df["Watts"])
    df["Estimated_Cost"] = df["Energy_kWh"] * 8.0
    df["Vampire_Cost"] = (df["Vampire_Watts"] / 1000 / 60) * 8.0
    df["CO2_kg"] = df["Energy_kWh"] * 0.4

    watts_std = df["Watts"].std()
    if watts_std == 0 or pd.isna(watts_std):
        df["Z_Score"] = 0
    else:
        df["Z_Score"] = (df["Watts"] - df["Watts"].mean()) / watts_std

    df["Is_Anomaly_Z"] = df["Z_Score"].abs() > 3

    return df

# =========================================================
# FILTERS
# =========================================================
def apply_filters(
    df, date_range, devices, categories, homes, day_types,
    times, watts_range, only_vampire_sources, only_anomalies
):
    out = df.copy()

    d0 = pd.Timestamp(date_range[0])
    d1 = pd.Timestamp(date_range[1])
    out = out[(out["Date"] >= d0) & (out["Date"] <= d1)]

    if devices:
        out = out[out["Device_Name"].isin(devices)]
    if categories:
        out = out[out["Category"].isin(categories)]
    if homes:
        out = out[out["Home_ID"].isin(homes)]
    if day_types:
        out = out[out["Day_Type"].isin(day_types)]
    if times:
        out = out[out["Time_of_Day"].isin(times)]

    out = out[(out["Watts"] >= watts_range[0]) & (out["Watts"] <= watts_range[1])]

    if only_vampire_sources:
        out = out[out["Is_Vampire_Source"] == True]

    if only_anomalies:
        out = out[out["Is_Anomaly_Z"] == True]

    return out

# =========================================================
# SIDEBAR
# =========================================================
def build_sidebar(df):
    c = get_theme_colors()

    with st.sidebar:
        st.markdown("### 🎨 Theme")
        is_dark = st.toggle(
            "Dark / Light Mode",
            value=(st.session_state.theme == "dark")
        )
        st.session_state.theme = "dark" if is_dark else "light"

        st.markdown("---")

        st.markdown(f"""
        <div style='text-align:center;padding:10px 0 18px 0;'>
            <div style='font-size:38px;'>⚡</div>
            <div style='font-size:16px;font-weight:700;color:{c["text"]};'>VampireVolt</div>
            <div style='font-size:11px;color:{c["subtext"]};'>Advanced Energy Waste Auditor</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        min_date = pd.to_datetime(df["Date"]).min().date()
        max_date = pd.to_datetime(df["Date"]).max().date()

        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(date_range) == 1:
            date_range = (date_range[0], max_date)

        devices = st.multiselect("Device", sorted(df["Device_Name"].dropna().unique().tolist()))
        categories = st.multiselect("Category", sorted(df["Category"].dropna().unique().tolist()))
        homes = st.multiselect("Home ID", sorted(df["Home_ID"].astype(str).dropna().unique().tolist()))
        day_types = st.multiselect("Day Type", sorted(df["Day_Type"].dropna().unique().tolist()))
        times = st.multiselect("Time of Day", sorted(df["Time_of_Day"].dropna().unique().tolist()))

        watts_min = float(df["Watts"].min())
        watts_max = float(df["Watts"].max())
        if watts_min == watts_max:
            watts_max = watts_min + 1

        watts_range = st.slider(
            "Watts Range",
            min_value=float(watts_min),
            max_value=float(watts_max),
            value=(float(watts_min), float(watts_max))
        )

        only_vampire_sources = st.checkbox("Only Vampire Source Devices")
        only_anomalies = st.checkbox("Only Z-Score Anomalies")

        st.markdown("---")
        st.markdown(f"""
        <div style='font-size:11px;color:{c["subtext"]};line-height:1.8;'>
            📅 {min_date} → {max_date}<br>
            📝 {len(df):,} readings<br>
            🔌 {df["Device_ID"].nunique()} devices<br>
            🏠 {df["Home_ID"].nunique()} homes
        </div>
        """, unsafe_allow_html=True)

    return date_range, devices, categories, homes, day_types, times, watts_range, only_vampire_sources, only_anomalies

# =========================================================
# SMART INSIGHTS
# =========================================================
def smart_insights(df):
    top_waste = df.groupby("Device_Name")["Vampire_Watts"].sum().sort_values(ascending=False)
    top_avg = df.groupby("Device_Name")["Watts"].mean().sort_values(ascending=False)

    weekday_kwh = df.loc[df["Day_Type"] == "Weekday", "Energy_kWh"].sum()
    weekend_kwh = df.loc[df["Day_Type"] == "Weekend", "Energy_kWh"].sum()

    total_energy = df["Energy_kWh"].sum()
    total_watts = df["Watts"].sum()
    vampire_watts = df["Vampire_Watts"].sum()
    vampire_ratio = (vampire_watts / total_watts * 100) if total_watts > 0 else 0
    peak_load = df["Watts"].max()
    avg_load = df["Watts"].mean()

    waste_device = top_waste.index[0] if not top_waste.empty else "N/A"
    waste_value = top_waste.iloc[0] if not top_waste.empty else 0

    avg_device = top_avg.index[0] if not top_avg.empty else "N/A"
    avg_value = top_avg.iloc[0] if not top_avg.empty else 0

    why_text = []

    if vampire_ratio >= 20:
        why_text.append(
            f"{waste_device} is contributing heavily to standby consumption, which means it may remain powered even when not actively used."
        )
    elif vampire_ratio >= 10:
        why_text.append(
            f"There is moderate standby waste, mainly driven by {waste_device}, which may be staying on for long hours."
        )
    else:
        why_text.append(
            f"Standby waste is relatively controlled, but {waste_device} is still the biggest contributor among selected devices."
        )

    if peak_load > avg_load * 2:
        why_text.append(
            "Peak load is much higher than average load, showing sudden usage spikes from heavy appliances."
        )

    if weekday_kwh > weekend_kwh:
        why_text.append(
            "Weekday energy is higher than weekend usage, suggesting appliances are used more during working days."
        )
    elif weekend_kwh > weekday_kwh:
        why_text.append(
            "Weekend energy is higher than weekday usage, suggesting longer appliance usage on non-working days."
        )

    why_final = " ".join(why_text)

    suggestion_text = (
        f"Start by checking {waste_device}. Turn it off completely when idle, use a smart plug, "
        f"and avoid keeping high-load appliances running unnecessarily."
    )

    recommendation_text = (
        f"Total selected energy is {total_energy:.2f} kWh. Reduce waste by lowering standby power, "
        f"spreading heavy appliance usage across the day, and monitoring night-time activity."
    )

    st.markdown("### 📌 Key Energy Insight")

    left, right = st.columns([1, 1])

    with left:
        st.info(
            f"🔌 **Highest standby waste device:**\n\n"
            f"{waste_device} with **{waste_value:.2f} W** of vampire load."
        )

        st.info(
            f"⚡ **Highest average load device:**\n\n"
            f"{avg_device} with **{avg_value:.2f} W** average power."
        )

        st.info(
            f"📅 **Weekday energy:** {weekday_kwh:.2f} kWh\n\n"
            f"**Weekend energy:** {weekend_kwh:.2f} kWh"
        )

    with right:
        st.info(
            f"🔌 **Why is it like this?:**\n\n"
            f"{why_final}"
        )

        st.info(
            f"⚡ **Suggestions**\n\n"
            f"{suggestion_text}"
        )

        st.info(
            f"📅 **Recommendations**\n\n"
            f"{recommendation_text}"
        )

# =========================================================
# EXECUTIVE TAB
# =========================================================
def tab_executive(df):
    c = get_theme_colors()
    layout = get_layout()

    total_kwh = df["Energy_kWh"].sum()
    baseline_power = df["Watts"].quantile(0.05)
    peak_load = df["Watts"].max()
    avg_load = df["Watts"].mean()
    total_watts = df["Watts"].sum()
    vampire_watts = df["Vampire_Watts"].sum()
    vampire_ratio = (vampire_watts / total_watts * 100) if total_watts else 0
    waste_cost = df["Vampire_Cost"].sum()
    total_cost = df["Estimated_Cost"].sum()
    anomaly_count = int(df["Is_Anomaly_Z"].sum())
    standby_hours = len(df[df["Is_Standby"]]) / 60

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(kpi_card("Total Energy", f"{total_kwh:.2f} kWh", "Total selected period"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Baseline Power", f"{baseline_power:.2f} W", "5th percentile power"), unsafe_allow_html=True)
    with c3:
        style = "bad" if vampire_ratio > 20 else "neutral" if vampire_ratio > 10 else "good"
        st.markdown(kpi_card("Vampire Ratio", f"{vampire_ratio:.1f}%", "Standby share", style), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Waste Cost", rupees(waste_cost), f"Total cost {rupees(total_cost)}", "bad"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Peak Load", f"{peak_load:.2f} W", f"Average {avg_load:.2f} W", "neutral"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi_card("Anomalies", f"{anomaly_count}", f"Standby hours {standby_hours:.1f}", "bad" if anomaly_count > 0 else "good"), unsafe_allow_html=True)

    section("Smart Insights")
    smart_insights(df)

    col1, col2 = st.columns([1, 2])

    with col1:
        section("Vampire Load Gauge")
        gauge_color = c["bad"] if vampire_ratio > 20 else c["warn"] if vampire_ratio > 10 else c["good"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=vampire_ratio,
            number={"suffix": "%", "font": {"size": 32, "color": gauge_color}},
            title={"text": "Vampire Load Ratio"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": gauge_color},
                "bgcolor": c["card"],
                "bordercolor": c["border"],
                "steps": [
                    {"range": [0, 10], "color": "rgba(34,197,94,0.15)"},
                    {"range": [10, 20], "color": "rgba(234,179,8,0.15)"},
                    {"range": [20, 100], "color": "rgba(239,68,68,0.15)"}
                ]
            }
        ))
        fig.update_layout(paper_bgcolor=c["plot_paper"], font_color=c["text"], height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("Top 10 Wasteful Devices")
        top10 = (
            df.groupby("Device_Name", as_index=False)["Vampire_Watts"]
            .sum()
            .sort_values("Vampire_Watts", ascending=False)
            .head(10)
        )
        fig_bar = px.bar(
            top10,
            x="Device_Name",
            y="Vampire_Watts",
            color="Vampire_Watts",
            color_continuous_scale="Reds",
            text_auto=".2f"
        )
        fig_bar.update_layout(**layout, height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    section("Daily Energy Trend")
    daily = df.groupby("Date", as_index=False).agg(
        Total_kWh=("Energy_kWh", "sum"),
        Vampire_kWh=("Vampire_Watts", lambda s: (s / 1000 / 60).sum())
    )
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=daily["Date"], y=daily["Total_kWh"], mode="lines+markers", name="Total kWh"))
    fig_line.add_trace(go.Scatter(x=daily["Date"], y=daily["Vampire_kWh"], mode="lines+markers", name="Vampire kWh"))
    fig_line.update_layout(**layout, height=340, yaxis_title="kWh")
    st.plotly_chart(fig_line, use_container_width=True)

    section("Home → Category → Device Sunburst")
    sun = df.groupby(["Home_ID", "Category", "Device_Name"], as_index=False)["Energy_kWh"].sum()
    fig_sun = px.sunburst(
        sun,
        path=["Home_ID", "Category", "Device_Name"],
        values="Energy_kWh",
        color="Energy_kWh",
        color_continuous_scale="RdYlBu_r"
    )
    fig_sun.update_layout(paper_bgcolor=c["plot_paper"], font_color=c["text"], height=500)
    st.plotly_chart(fig_sun, use_container_width=True)

# =========================================================
# LOAD ANALYSIS TAB
# =========================================================
def tab_load_analysis(df):
    c = get_theme_colors()
    layout = get_layout()

    baseline = df["Watts"].quantile(0.05)

    section("24-Hour Load Profile")
    hourly = df.groupby("Hour", as_index=False).agg(
        Total_Watts=("Watts", "mean"),
        Active_Watts=("Active_Watts", "mean"),
        Vampire_Watts=("Vampire_Watts", "mean")
    )

    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=hourly["Hour"], y=hourly["Total_Watts"], name="Total Watts", fill="tozeroy"))
    fig_area.add_trace(go.Scatter(x=hourly["Hour"], y=hourly["Vampire_Watts"], name="Vampire Watts", fill="tozeroy"))
    fig_area.add_hline(y=baseline, line_dash="dash", line_color=c["blue2"], annotation_text=f"Baseline {baseline:.2f}W")
    fig_area.update_layout(**layout, height=350, xaxis_title="Hour", yaxis_title="Average Watts")
    st.plotly_chart(fig_area, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        section("Heatmap: Hour vs Day")
        heat = df.groupby(["Day_Name", "Hour"], as_index=False)["Watts"].mean()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat["Day_Name"] = pd.Categorical(heat["Day_Name"], categories=order, ordered=True)
        heat = heat.sort_values(["Day_Name", "Hour"])
        pivot = heat.pivot(index="Day_Name", columns="Hour", values="Watts")

        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Hour", y="Day", color="Avg Watts"),
            aspect="auto",
            color_continuous_scale="RdYlBu_r"
        )
        fig_heat.update_layout(
            paper_bgcolor=c["plot_paper"],
            plot_bgcolor=c["plot_bg"],
            font_color=c["text"],
            height=400
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col2:
        section("Weekday vs Weekend")
        comp = df.groupby("Day_Type", as_index=False).agg(
            Total_kWh=("Energy_kWh", "sum"),
            Vampire_kWh=("Vampire_Watts", lambda s: (s / 1000 / 60).sum())
        )
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=comp["Day_Type"], y=comp["Total_kWh"], name="Total kWh"))
        fig_comp.add_trace(go.Bar(x=comp["Day_Type"], y=comp["Vampire_kWh"], name="Vampire kWh"))
        fig_comp.update_layout(**layout, height=400, barmode="group")
        st.plotly_chart(fig_comp, use_container_width=True)

    section("Power Distribution by Device")
    fig_box = px.box(
        df,
        x="Device_Name",
        y="Watts",
        color="Category",
        color_discrete_sequence=get_colors()
    )
    fig_box.update_layout(**layout, height=420)
    st.plotly_chart(fig_box, use_container_width=True)

# =========================================================
# ANOMALY TAB
# =========================================================
def tab_anomaly(df):
    c = get_theme_colors()
    layout = get_layout()

    device_stats = df.groupby(["Device_Name", "Category", "Standby_Threshold_Watts"], as_index=False).agg(
        Avg_Watts=("Watts", "mean"),
        Max_Watts=("Watts", "max"),
        Vampire_Watts=("Vampire_Watts", "sum"),
        Total_Watts=("Watts", "sum"),
        Readings=("Reading_Key", "count")
    )
    device_stats["Vampire_Ratio"] = np.where(
        device_stats["Total_Watts"] > 0,
        device_stats["Vampire_Watts"] / device_stats["Total_Watts"] * 100,
        0
    )
    device_stats["Anomaly_Device"] = device_stats["Max_Watts"] > (device_stats["Standby_Threshold_Watts"] * 2)

    col1, col2 = st.columns([2, 1])

    with col1:
        section("Scatter: Avg Watts vs Threshold")
        fig_scatter = px.scatter(
            device_stats,
            x="Standby_Threshold_Watts",
            y="Avg_Watts",
            size="Vampire_Watts",
            color="Category",
            hover_data=["Device_Name", "Max_Watts", "Vampire_Ratio", "Readings"],
            text="Device_Name",
            color_discrete_sequence=get_colors()
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(**layout, height=450)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col2:
        section("Anomaly Summary")
        total_anomalies = int(df["Is_Anomaly_Z"].sum())
        anomaly_devices = int(device_stats["Anomaly_Device"].sum())
        st.markdown(kpi_card("Z-Score Anomalies", str(total_anomalies), "Readings with |Z| > 3", "bad"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(kpi_card("Risk Devices", str(anomaly_devices), "Devices exceeding threshold", "neutral"), unsafe_allow_html=True)

    section("Wall of Shame")
    shame = device_stats.sort_values(["Vampire_Watts", "Vampire_Ratio"], ascending=False).copy()
    shame["Action"] = np.where(
        shame["Vampire_Ratio"] > 50,
        "Unplug / Smart Plug",
        np.where(shame["Vampire_Ratio"] > 20, "Monitor Standby", "Normal")
    )
    st.dataframe(
        shame[[
            "Device_Name", "Category", "Standby_Threshold_Watts",
            "Avg_Watts", "Max_Watts", "Vampire_Watts",
            "Vampire_Ratio", "Readings", "Action"
        ]],
        use_container_width=True,
        hide_index=True
    )

    section("Treemap: Waste Contribution")
    tree_df = df.groupby(["Category", "Device_Name"], as_index=False)["Vampire_Watts"].sum()
    fig_tree = px.treemap(
        tree_df,
        path=["Category", "Device_Name"],
        values="Vampire_Watts",
        color="Vampire_Watts",
        color_continuous_scale="Reds"
    )
    fig_tree.update_layout(
        paper_bgcolor=c["plot_paper"],
        font_color=c["text"],
        height=480,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_tree, use_container_width=True)

# =========================================================
# COMPARISON TAB
# =========================================================
def tab_comparison(df):
    c = get_theme_colors()
    layout = get_layout()

    col1, col2 = st.columns(2)

    with col1:
        section("Home-wise Energy Comparison")
        home_df = df.groupby("Home_ID", as_index=False).agg(
            Total_kWh=("Energy_kWh", "sum"),
            Waste_Cost=("Vampire_Cost", "sum")
        )
        fig_home = px.bar(
            home_df,
            x="Home_ID",
            y="Total_kWh",
            color="Waste_Cost",
            color_continuous_scale="Sunsetdark",
            text_auto=".2f"
        )
        fig_home.update_layout(**layout, height=380)
        st.plotly_chart(fig_home, use_container_width=True)

    with col2:
        section("Category-wise Cost Split")
        cat_df = df.groupby("Category", as_index=False).agg(
            Total_Cost=("Estimated_Cost", "sum"),
            Waste_Cost=("Vampire_Cost", "sum")
        )
        fig_donut = go.Figure(data=[go.Pie(
            labels=cat_df["Category"],
            values=cat_df["Waste_Cost"],
            hole=0.55
        )])
        fig_donut.update_layout(
            paper_bgcolor=c["plot_paper"],
            plot_bgcolor=c["plot_paper"],
            font=dict(color=c["text"]),
            height=380
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    section("Day vs Night Analysis")
    dn = df.copy()
    dn["Mode"] = np.where(dn["Hour"].between(6, 18), "Day", "Night")
    daynight = dn.groupby("Mode", as_index=False).agg(
        Total_kWh=("Energy_kWh", "sum"),
        Vampire_kWh=("Vampire_Watts", lambda s: (s / 1000 / 60).sum())
    )
    fig_dn = go.Figure()
    fig_dn.add_trace(go.Bar(x=daynight["Mode"], y=daynight["Total_kWh"], name="Total kWh"))
    fig_dn.add_trace(go.Bar(x=daynight["Mode"], y=daynight["Vampire_kWh"], name="Vampire kWh"))
    fig_dn.update_layout(**layout, height=360, barmode="group")
    st.plotly_chart(fig_dn, use_container_width=True)

# =========================================================
# EXPORT TAB
# =========================================================
def tab_export(df):
    section("Export Filtered Data")

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Current Filtered Dataset",
        data=csv_data,
        file_name="vampirevolt_filtered_data.csv",
        mime="text/csv"
    )

    section("Export Anomaly Data")
    anom = df[df["Is_Anomaly_Z"] == True].copy()
    anom_csv = anom.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Anomaly Readings",
        data=anom_csv,
        file_name="vampirevolt_anomalies.csv",
        mime="text/csv"
    )

    section("Preview")
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)

# =========================================================
# AI INSIGHTS
# =========================================================
def generate_ai_insights(df):
    total_kwh = round(df["Energy_kWh"].sum(), 2)

    total_watts = df["Watts"].sum()
    vampire_watts = df["Vampire_Watts"].sum()
    vampire_ratio = round((vampire_watts / total_watts) * 100, 2) if total_watts else 0

    anomaly_count = int(df["Is_Anomaly_Z"].sum())
    waste_cost = round(df["Vampire_Cost"].sum(), 2)

    top_device_series = (
        df.groupby("Device_Name")["Vampire_Watts"]
        .sum()
        .sort_values(ascending=False)
    )
    top_waste_device = top_device_series.index[0] if not top_device_series.empty else "N/A"

    prompt = f"""
    You are an energy analytics expert.

    Analyze this energy dataset:

    Total Energy: {total_kwh} kWh
    Vampire Load Ratio: {vampire_ratio}%
    Anomalies: {anomaly_count}
    Waste Cost: ₹{waste_cost}
    Top Waste Device: {top_waste_device}

    Provide:
    - Key Problems
    - Important Insights
    - 5 Actionable Recommendations
    - Final Advice
    """

    if client is None:
        return "⚠️ API_KEY not found. Add your Groq API key in a .env file like: API_KEY=your_key_here"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error generating insights: {e}"

def tab_chatbot(df):
    section("AI Insights")
    st.subheader("🤖 AI Energy Insights")

    c = get_theme_colors()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Generate AI Insights", use_container_width=True):
            with st.spinner("Analyzing energy patterns..."):
                st.session_state.insights = generate_ai_insights(df)

    with col2:
        if st.button("♻️ Clear Insights", use_container_width=True):
            st.session_state.insights = ""

    with col3:
        st.info("Uses Groq API for summary")

    if st.session_state.insights:
        st.markdown(
            f"""
            <div style="
                background:{c["card"]};
                border:1px solid {c["border"]};
                border-radius:16px;
                padding:18px;
                margin-top:12px;
                line-height:1.8;
            ">
            """,
            unsafe_allow_html=True
        )
        st.write(st.session_state.insights)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Click 'Generate AI Insights' to create an intelligent summary for the selected filtered data.")

# =========================================================
# ABOUT PAGE
# =========================================================
def about_page():
    st.markdown("""
    <div style="text-align:center;padding:40px;">
        <h1 style="font-size:48px;">⚡ VampireVolt</h1>
        <p>Intelligent Energy Waste Auditor</p>
    </div>
    """, unsafe_allow_html=True)

    st.image(
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
        use_container_width=True
    )

    st.markdown("## 📌 About Application")
    st.markdown("""
    VampireVolt is an advanced energy analytics dashboard that helps detect hidden energy wastage caused by standby power consumption.

    ### 🚨 Problem
    Devices consume electricity even when turned off, which creates vampire load and increases energy bills.

    ### 💡 Solution
    - Detect standby power
    - Identify waste devices
    - Analyze energy trends
    - Provide smart insights
    - Generate AI-based recommendations

    ### 🎯 Goal
    Reduce electricity cost and improve efficiency.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🔌 Detect Vampire Loads")
    with col2:
        st.info("📊 Visual Analytics")
    with col3:
        st.info("🤖 AI Insights")

# =========================================================
# DASHBOARD PAGE
# =========================================================
def dashboard_page():
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure all CSV files are present in the same folder as app.py.")
        return

    (
        date_range, devices, categories, homes, day_types,
        times, watts_range, only_vampire_sources, only_anomalies
    ) = build_sidebar(df)

    filtered = apply_filters(
        df,
        date_range,
        devices,
        categories,
        homes,
        day_types,
        times,
        watts_range,
        only_vampire_sources,
        only_anomalies
    )

    st.markdown("""
    <div class="banner">
        <div class="banner-title">⚡ VampireVolt: Intelligent Energy Waste Auditor</div>
        <div class="banner-sub">Advanced Streamlit analytics dashboard for standby power, anomalies, device efficiency, and energy waste insights.</div>
    </div>
    """, unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Executive Summary",
        "Load Analysis",
        "Anomaly Profiler",
        "Comparison",
        "Export",
        "AI Insights"
    ])

    with tab1:
        tab_executive(filtered)
    with tab2:
        tab_load_analysis(filtered)
    with tab3:
        tab_anomaly(filtered)
    with tab4:
        tab_comparison(filtered)
    with tab5:
        tab_export(filtered)
    with tab6:
        tab_chatbot(filtered)

    st.markdown("---")
    st.caption("Built with Streamlit • VampireVolt Energy Analytics Dashboard")

# =========================================================
# MAIN
# =========================================================
def main():
    apply_custom_css()

    st.sidebar.title("⚡ VampireVolt")
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 About Application", "📊 Dashboard"]
    )

    if page == "🏠 About Application":
        about_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()