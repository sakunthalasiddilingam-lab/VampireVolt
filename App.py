import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="VampireVolt Energy Auditor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, .stApp { background-color: #0d1117; color: #e6edf3; font-family: 'Segoe UI', sans-serif; }
section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 12px; }

.kpi-card {
    background: linear-gradient(145deg,#1c2128 0%,#161b22 100%);
    border: 1px solid #30363d; border-radius: 14px;
    padding: 22px 18px; text-align: center;
    box-shadow: 0 6px 24px rgba(0,0,0,0.45);
    transition: transform .2s, box-shadow .2s;
    height: 130px; display: flex; flex-direction: column; justify-content: center;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 32px rgba(0,0,0,0.6); }
.kpi-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.1px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #f0f6fc; line-height: 1.1; }
.kpi-sub   { font-size: 12px; margin-top: 6px; }
.kpi-sub.good    { color: #3fb950; }
.kpi-sub.bad     { color: #f85149; }
.kpi-sub.neutral { color: #d29922; }

.alert-red    { background:#2d1117; border-left:4px solid #f85149; border-radius:8px; padding:12px 16px; margin:5px 0; color:#ff7b72; font-size:13px; }
.alert-yellow { background:#2d2208; border-left:4px solid #d29922; border-radius:8px; padding:12px 16px; margin:5px 0; color:#e3b341; font-size:13px; }
.alert-green  { background:#0d2a1a; border-left:4px solid #3fb950; border-radius:8px; padding:12px 16px; margin:5px 0; color:#56d364; font-size:13px; }
.alert-blue   { background:#0d1b2e; border-left:4px solid #388bfd; border-radius:8px; padding:12px 16px; margin:5px 0; color:#79c0ff; font-size:13px; }

.section-title {
    font-size: 16px; font-weight: 700; color: #f0f6fc;
    border-bottom: 2px solid #21262d; padding-bottom: 8px;
    margin: 18px 0 12px 0; text-transform: uppercase; letter-spacing: 0.5px;
}

.page-banner {
    background: linear-gradient(90deg,#1f2d3d 0%,#1c2128 100%);
    border: 1px solid #30363d; border-radius: 12px;
    padding: 18px 24px; margin-bottom: 20px;
}
.page-banner h1 { font-size: 22px; font-weight: 700; color: #f0f6fc; margin: 0; }
.page-banner p  { font-size: 13px; color: #8b949e; margin: 4px 0 0 0; }
</style>
""", unsafe_allow_html=True)

DARK_LAYOUT = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="Segoe UI"),
    xaxis=dict(gridcolor="#21262d", showgrid=True, linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", showgrid=True, linecolor="#30363d"),
    margin=dict(l=30, r=20, t=50, b=30),
    legend=dict(bgcolor="#1c2128", bordercolor="#30363d", borderwidth=1)
)

COLORS = ["#388bfd","#3fb950","#d29922","#f85149","#a5d6ff",
          "#56d364","#e3b341","#ff7b72","#79c0ff","#7ee787"]

def kpi_card(label, value, sub="", sub_class="neutral"):
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub {sub_class}">{sub}</div>
    </div>"""

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def alert(msg, kind="blue"):
    st.markdown(f'<div class="alert-{kind}">{msg}</div>', unsafe_allow_html=True)

def fmt_number(v):
    if pd.isna(v):
        return "0"
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.0f}"

def fmt_currency(v):
    return f"₹{v:,.0f}"

@st.cache_data
def load_data():
    fact = pd.read_csv("FactEnergyConsumption.csv")
    dim_appliance = pd.read_csv("DimAppliance.csv")
    dim_date = pd.read_csv("DimDate.csv")
    dim_home = pd.read_csv("DimHomeProfile.csv")

    fact["Timestamp"] = pd.to_datetime(fact["Timestamp"], errors="coerce")
    dim_date["Timestamp"] = pd.to_datetime(dim_date["Timestamp"], errors="coerce")
    dim_date["Date"] = pd.to_datetime(dim_date["Date"], errors="coerce")

    master = (
        fact.merge(dim_appliance, on="Device_ID", how="left")
            .merge(dim_home, on="Home_ID", how="left")
            .merge(dim_date, on="Timestamp", how="left")
    )

    master["Date"] = pd.to_datetime(master["Date"], errors="coerce")
    master["Standby_Threshold_Watts"] = pd.to_numeric(master["Standby_Threshold_Watts"], errors="coerce").fillna(0)
    master["Watts"] = pd.to_numeric(master["Watts"], errors="coerce").fillna(0)
    master["Volts"] = pd.to_numeric(master["Volts"], errors="coerce").fillna(0)
    master["Amps"] = pd.to_numeric(master["Amps"], errors="coerce").fillna(0)

    master["Energy_kWh"] = master["Watts"] / 1000 / 60
    master["Baseline_Candidate"] = np.where(master["Hour"].between(0, 5), master["Watts"], np.nan)
    master["Is_Standby"] = master["Watts"] <= master["Standby_Threshold_Watts"]
    master["Vampire_Watts"] = np.where(master["Is_Standby"], master["Watts"], 0)
    master["Active_Watts"] = np.where(master["Is_Standby"], 0, master["Watts"])
    master["Estimated_Cost"] = master["Energy_kWh"] * 8.0
    master["Vampire_Cost"] = (master["Vampire_Watts"] / 1000 / 60) * 8.0
    master["CO2_kg"] = master["Energy_kWh"] * 0.4
    return master, dim_appliance, dim_home

def apply_filters(df, date_range, devices, categories, homes, day_types, time_of_day):
    d0 = pd.Timestamp(date_range[0])
    d1 = pd.Timestamp(date_range[1])
    out = df[(df["Date"] >= d0) & (df["Date"] <= d1)].copy()

    if devices:
        out = out[out["Device_Name"].isin(devices)]
    if categories:
        out = out[out["Category"].isin(categories)]
    if homes:
        out = out[out["Home_ID"].isin(homes)]
    if day_types:
        out = out[out["Day_Type"].isin(day_types)]
    if time_of_day:
        out = out[out["Time_of_Day"].isin(time_of_day)]
    return out

def page_executive(df):
    st.markdown("""<div class="page-banner">
        <h1>⚡ Executive Auditor Summary</h1>
        <p>High-level view of energy use, baseline load, vampire load, cost, and environmental impact</p>
    </div>""", unsafe_allow_html=True)

    total_kwh = df["Energy_kWh"].sum()
    baseline_power = df["Watts"].quantile(0.05)
    vampire_watts = df["Vampire_Watts"].sum()
    total_watts = df["Watts"].sum()
    vampire_ratio = (vampire_watts / total_watts * 100) if total_watts else 0
    waste_cost = df["Vampire_Cost"].sum()
    total_cost = df["Estimated_Cost"].sum()
    co2 = df["CO2_kg"].sum()

    anomaly_threshold = baseline_power * 2
    anomaly_count = int((df["Watts"] > anomaly_threshold).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card("Total Energy", f"{total_kwh:,.2f} kWh", "Total consumption"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Baseline Power", f"{baseline_power:,.2f} W", "5th percentile floor"), unsafe_allow_html=True)
    with c3:
        sc = "bad" if vampire_ratio > 20 else ("neutral" if vampire_ratio > 10 else "good")
        st.markdown(kpi_card("Vampire Ratio", f"{vampire_ratio:.1f}%", "Standby share", sc), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Waste Cost", fmt_currency(waste_cost), f"Total cost {fmt_currency(total_cost)}", "bad" if waste_cost > 100 else "neutral"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Carbon Impact", f"{co2:,.2f} kg", f"Anomalies: {anomaly_count}", "neutral"), unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        section("VAMPIRE LOAD GAUGE")
        gauge_color = "#f85149" if vampire_ratio > 20 else ("#d29922" if vampire_ratio > 10 else "#3fb950")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=vampire_ratio,
            number={"suffix": "%", "font": {"color": gauge_color, "size": 34}},
            title={"text": "Vampire Load Ratio", "font": {"color": "#c9d1d9", "size": 13}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#8b949e"},
                "bar": {"color": gauge_color},
                "bgcolor": "#161b22",
                "borderwidth": 1,
                "bordercolor": "#30363d",
                "steps": [
                    {"range": [0, 10], "color": "#0d2a1a"},
                    {"range": [10, 20], "color": "#2d2208"},
                    {"range": [20, 100], "color": "#2d1117"},
                ],
            }
        ))
        fig.update_layout(paper_bgcolor="#0d1117", font_color="#c9d1d9", height=320, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("DEVICE WASTE CONTRIBUTION")
        dev = df.groupby("Device_Name", as_index=False).agg(
            Total_Watts=("Watts", "sum"),
            Vampire_Watts=("Vampire_Watts", "sum")
        )
        dev["Vampire_Ratio"] = np.where(dev["Total_Watts"] > 0, dev["Vampire_Watts"] / dev["Total_Watts"] * 100, 0)
        dev = dev.sort_values("Vampire_Watts", ascending=False)

        fig_bar = go.Figure(go.Bar(
            x=dev["Device_Name"],
            y=dev["Vampire_Watts"],
            marker_color=["#f85149" if x > dev["Vampire_Watts"].mean() else "#388bfd" for x in dev["Vampire_Watts"]],
            text=[f"{v:,.0f}" for v in dev["Vampire_Watts"]],
            textposition="outside"
        ))
        fig_bar.update_layout(**DARK_LAYOUT, height=320, showlegend=False, yaxis_title="Vampire Watts", xaxis_title="Device")
        st.plotly_chart(fig_bar, use_container_width=True)

    section("DAILY ENERGY CONSUMPTION")
    daily = df.groupby("Date", as_index=False).agg(
        Total_kWh=("Energy_kWh", "sum"),
        Vampire_kWh=("Vampire_Watts", lambda s: (s / 1000 / 60).sum())
    ).sort_values("Date")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=daily["Date"], y=daily["Total_kWh"], mode="lines", name="Total kWh", line=dict(color="#388bfd", width=2)))
    fig_line.add_trace(go.Scatter(x=daily["Date"], y=daily["Vampire_kWh"], mode="lines", name="Vampire kWh", line=dict(color="#f85149", width=2)))
    fig_line.update_layout(**DARK_LAYOUT, height=320, yaxis_title="kWh")
    st.plotly_chart(fig_line, use_container_width=True)

    section("RECOMMENDATIONS")
    if vampire_ratio > 20:
        alert("🔴 High vampire load detected. Focus on standby-heavy devices like chargers, TVs, routers, and lights.", "red")
    elif vampire_ratio > 10:
        alert("🟡 Moderate standby waste detected. You can reduce waste by switching off non-essential devices at night.", "yellow")
    else:
        alert("🟢 Standby consumption looks controlled in the selected period.", "green")

    if anomaly_count > 0:
        alert(f"⚠️ {anomaly_count} readings are above 2× baseline power. Check unusual spikes or malfunctioning devices.", "blue")

def page_load_analysis(df):
    st.markdown("""<div class="page-banner">
        <h1>📈 High-Frequency Load Analysis</h1>
        <p>See active load vs phantom load over time, plus hourly and weekday patterns</p>
    </div>""", unsafe_allow_html=True)

    baseline_power = df["Watts"].quantile(0.05)

    hourly = df.groupby("Hour", as_index=False).agg(
        Total_Watts=("Watts", "mean"),
        Active_Watts=("Active_Watts", "mean"),
        Vampire_Watts=("Vampire_Watts", "mean")
    )

    section("24-HOUR LOAD PROFILE")
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=hourly["Hour"], y=hourly["Total_Watts"], fill="tozeroy", name="Average Total Watts", line=dict(color="#388bfd", width=2)))
    fig_area.add_trace(go.Scatter(x=hourly["Hour"], y=hourly["Vampire_Watts"], fill="tozeroy", name="Average Vampire Watts", line=dict(color="#f85149", width=2)))
    fig_area.add_hline(y=baseline_power, line_color="#79c0ff", line_dash="dash", annotation_text=f"Baseline {baseline_power:.1f}W")
    fig_area.update_layout(**DARK_LAYOUT, height=340, xaxis_title="Hour of Day", yaxis_title="Average Watts")
    st.plotly_chart(fig_area, use_container_width=True)

    section("HEATMAP: HOUR vs DAY OF WEEK")
    heat = df.groupby(["Day_Name", "Hour"], as_index=False)["Watts"].mean()
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat["Day_Name"] = pd.Categorical(heat["Day_Name"], categories=day_order, ordered=True)
    heat = heat.sort_values(["Day_Name","Hour"])
    pivot = heat.pivot(index="Day_Name", columns="Hour", values="Watts")

    fig_heat = px.imshow(
        pivot,
        labels=dict(x="Hour", y="Day", color="Avg Watts"),
        aspect="auto",
        color_continuous_scale=["#0d2a1a", "#d29922", "#f85149"]
    )
    fig_heat.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9"),
        height=380,
        margin=dict(l=20,r=20,t=40,b=20)
    )
    st.plotly_chart(fig_heat, use_container_width=True)

def page_anomaly_profiler(df):
    st.markdown("""<div class="page-banner">
        <h1>🔍 Anomaly & Efficiency Profiler</h1>
        <p>Identify wasteful devices, standby-heavy appliances, and outlier power behavior</p>
    </div>""", unsafe_allow_html=True)

    baseline_power = df["Watts"].quantile(0.05)
    anomaly_threshold = baseline_power * 2

    device_stats = df.groupby(["Device_Name", "Category", "Standby_Threshold_Watts"], as_index=False).agg(
        Avg_Watts=("Watts", "mean"),
        Max_Watts=("Watts", "max"),
        Vampire_Watts=("Vampire_Watts", "sum"),
        Total_Watts=("Watts", "sum"),
        Readings=("Reading_Key", "count")
    )
    device_stats["Vampire_Ratio"] = np.where(device_stats["Total_Watts"] > 0, device_stats["Vampire_Watts"] / device_stats["Total_Watts"] * 100, 0)
    device_stats["Is_Anomaly_Device"] = device_stats["Max_Watts"] > (device_stats["Standby_Threshold_Watts"] * 2)

    col1, col2 = st.columns([2, 1])

    with col1:
        section("SCATTER: AVG WATTS vs STANDBY THRESHOLD")
        fig_scatter = px.scatter(
            device_stats,
            x="Standby_Threshold_Watts",
            y="Avg_Watts",
            size="Vampire_Watts",
            color="Category",
            hover_data=["Device_Name", "Max_Watts", "Vampire_Ratio", "Readings"],
            text="Device_Name",
            color_discrete_sequence=COLORS
        )
        fig_scatter.add_shape(
            type="line",
            x0=device_stats["Standby_Threshold_Watts"].min(),
            y0=device_stats["Standby_Threshold_Watts"].min(),
            x1=device_stats["Standby_Threshold_Watts"].max(),
            y1=device_stats["Standby_Threshold_Watts"].max(),
            line=dict(color="#79c0ff", dash="dash")
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(**DARK_LAYOUT, height=420, xaxis_title="Standby Threshold (W)", yaxis_title="Average Watts")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col2:
        section("ANOMALY SNAPSHOT")
        anomaly_count = int((df["Watts"] > anomaly_threshold).sum())
        standby_count = int(df["Is_Standby"].sum())
        st.markdown(kpi_card("Anomaly Readings", fmt_number(anomaly_count), f"Threshold: {anomaly_threshold:.1f} W", "bad" if anomaly_count > 0 else "good"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(kpi_card("Standby Readings", fmt_number(standby_count), "Readings below threshold", "neutral"), unsafe_allow_html=True)

    section("WALL OF SHAME")
    shame = device_stats.sort_values(["Vampire_Watts", "Vampire_Ratio"], ascending=False).copy()
    shame["Vampire_Watts"] = shame["Vampire_Watts"].round(2)
    shame["Avg_Watts"] = shame["Avg_Watts"].round(2)
    shame["Max_Watts"] = shame["Max_Watts"].round(2)
    shame["Vampire_Ratio"] = shame["Vampire_Ratio"].round(2)
    shame["Action"] = np.where(shame["Vampire_Ratio"] > 50, "Unplug / smart switch",
                        np.where(shame["Vampire_Ratio"] > 20, "Monitor standby", "Normal"))
    st.dataframe(
        shame[["Device_Name", "Category", "Standby_Threshold_Watts", "Avg_Watts", "Max_Watts", "Vampire_Watts", "Vampire_Ratio", "Action"]],
        use_container_width=True,
        hide_index=True
    )

def page_chatbot(df):
    st.markdown("""<div class="page-banner">
        <h1>🤖 Energy Insights Chatbot</h1>
        <p>Ask questions about energy usage, vampire load, anomalies, and device behavior</p>
    </div>""", unsafe_allow_html=True)

    baseline_power = df["Watts"].quantile(0.05)
    total_kwh = df["Energy_kWh"].sum()
    vampire_watts = df["Vampire_Watts"].sum()
    total_watts = df["Watts"].sum()
    vampire_ratio = (vampire_watts / total_watts * 100) if total_watts else 0
    waste_cost = df["Vampire_Cost"].sum()
    anomaly_count = int((df["Watts"] > baseline_power * 2).sum())

    device_stats = df.groupby("Device_Name", as_index=False).agg(
        Avg_Watts=("Watts", "mean"),
        Vampire_Watts=("Vampire_Watts", "sum"),
        Total_Watts=("Watts", "sum")
    )
    device_stats["Vampire_Ratio"] = np.where(device_stats["Total_Watts"] > 0, device_stats["Vampire_Watts"] / device_stats["Total_Watts"] * 100, 0)
    top_waste_device = device_stats.sort_values("Vampire_Watts", ascending=False).iloc[0]["Device_Name"]
    top_ratio_device = device_stats.sort_values("Vampire_Ratio", ascending=False).iloc[0]["Device_Name"]

    def respond(msg):
        q = msg.lower()

        if "summary" in q or "overview" in q or "status" in q:
            return f"""
### Energy Summary
- Total Energy: **{total_kwh:,.2f} kWh**
- Baseline Power: **{baseline_power:,.2f} W**
- Vampire Ratio: **{vampire_ratio:.1f}%**
- Waste Cost: **{fmt_currency(waste_cost)}**
- Anomaly Count: **{anomaly_count}**
- Top Waste Device: **{top_waste_device}**
"""

        if "vampire" in q or "standby" in q or "waste" in q:
            return f"""
### Vampire Load Analysis
- Vampire Ratio is **{vampire_ratio:.1f}%**
- Total standby waste cost is **{fmt_currency(waste_cost)}**
- Biggest standby energy contributor: **{top_waste_device}**
- Highest standby ratio device: **{top_ratio_device}**
"""

        if "anomaly" in q or "spike" in q:
            return f"""
### Anomaly Analysis
- Baseline Power: **{baseline_power:,.2f} W**
- Anomaly threshold used: **{baseline_power*2:,.2f} W**
- Total anomaly readings: **{anomaly_count}**
"""

        if "device" in q and ("highest" in q or "top" in q or "waste" in q):
            return f"Top wasteful device is **{top_waste_device}**. Highest standby ratio device is **{top_ratio_device}**."

        if "help" in q or "hello" in q or "hi" in q:
            return """
I can answer things like:
- Give me summary
- Which device has highest vampire load?
- Show anomaly count
- What is the standby waste?
"""

        return f"Current vampire ratio is **{vampire_ratio:.1f}%** and top waste device is **{top_waste_device}**."

    if "energy_chat" not in st.session_state:
        st.session_state.energy_chat = [
            {"role": "assistant", "content": "Hello! Ask me about total energy, vampire load, waste cost, anomalies, or devices."}
        ]

    for msg in st.session_state.energy_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    q1, q2, q3, q4 = st.columns(4)
    quick = ["Give me summary", "Which device has highest vampire load?", "Show anomaly count", "What is the standby waste?"]
    for i, col in enumerate([q1, q2, q3, q4]):
        with col:
            if st.button(quick[i], use_container_width=True):
                st.session_state.energy_chat.append({"role": "user", "content": quick[i]})
                st.session_state.energy_chat.append({"role": "assistant", "content": respond(quick[i])})
                st.rerun()

    prompt = st.chat_input("Ask about your energy data...")
    if prompt:
        st.session_state.energy_chat.append({"role": "user", "content": prompt})
        st.session_state.energy_chat.append({"role": "assistant", "content": respond(prompt)})
        st.rerun()

    if st.button("Clear Chat"):
        st.session_state.energy_chat = [{"role": "assistant", "content": "Chat cleared. Ask a new question."}]
        st.rerun()

def build_sidebar(df):
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:10px 0 20px 0;'>
            <div style='font-size:36px;'>⚡</div>
            <div style='font-size:15px;font-weight:700;color:#f0f6fc;'>VampireVolt</div>
            <div style='font-size:11px;color:#8b949e;'>Intelligent Energy Waste Auditor</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        page = st.selectbox("Navigation", [
            "Executive Auditor Summary",
            "High-Frequency Load Analysis",
            "Anomaly & Efficiency Profiler",
            "AI Chatbot"
        ])

        st.markdown("---")

        min_d = df["Date"].min().date()
        max_d = df["Date"].max().date()

        date_range = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        if len(date_range) == 1:
            date_range = (date_range[0], max_d)

        devices = st.multiselect("Device", sorted(df["Device_Name"].dropna().unique().tolist()))
        categories = st.multiselect("Category", sorted(df["Category"].dropna().unique().tolist()))
        homes = st.multiselect("Home ID", sorted(df["Home_ID"].dropna().unique().tolist()))
        day_types = st.multiselect("Day Type", sorted(df["Day_Type"].dropna().unique().tolist()))
        time_of_day = st.multiselect("Time of Day", sorted(df["Time_of_Day"].dropna().unique().tolist()))

        st.markdown("---")
        st.markdown(f"""
        <div style='font-size:11px;color:#6e7681;padding:6px 0;line-height:1.8;'>
            📅 {min_d} → {max_d}<br>
            📝 {len(df):,} readings<br>
            🔌 {df["Device_ID"].nunique()} devices<br>
            🏠 {df["Home_ID"].nunique()} homes
        </div>""", unsafe_allow_html=True)

    return page, date_range, devices, categories, homes, day_types, time_of_day

def main():
    with st.spinner("Loading energy datasets..."):
        df, dim_appliance, dim_home = load_data()

    page, date_range, devices, categories, homes, day_types, time_of_day = build_sidebar(df)
    filtered = apply_filters(df, date_range, devices, categories, homes, day_types, time_of_day)

    if filtered.empty:
        st.warning("No data found for the selected filters.")
        return

    if page == "Executive Auditor Summary":
        page_executive(filtered)
    elif page == "High-Frequency Load Analysis":
        page_load_analysis(filtered)
    elif page == "Anomaly & Efficiency Profiler":
        page_anomaly_profiler(filtered)
    elif page == "AI Chatbot":
        page_chatbot(filtered)

if __name__ == "__main__":
    main()