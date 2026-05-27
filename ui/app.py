"""
JR Commute — AI-Powered Smart City Commute Planner
Multi-page navigation with home + sub-pages.
"""
import sys
import time
import logging
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go

logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="JR Commute",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

.stApp { background: #060d1f; }
.main .block-container { padding-top: 0; max-width: 1400px; }
.stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp li { color: #e2e8f0; }
h1,h2,h3,h4,h5,h6 { color: #f8fafc !important; }

/* ── Top nav bar ── */
.topbar {
    background: linear-gradient(135deg, #0f1f40, #130f2e);
    border-bottom: 1px solid rgba(99,102,241,0.25);
    padding: 14px 32px;
    display: flex; align-items: center; justify-content: space-between;
    position: relative; overflow: hidden;
}
.topbar::after {
    content:''; position:absolute; top:-80px; right:-60px;
    width:280px; height:280px;
    background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%);
    border-radius:50%; pointer-events:none;
}
.topbar-brand { display:flex; align-items:center; gap:14px; }
.topbar-badge {
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    border-radius:12px; width:44px; height:44px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.3rem; font-weight:800; color:#fff;
    box-shadow:0 4px 14px rgba(99,102,241,0.4); flex-shrink:0;
}
.topbar-name {
    font-size:1.5rem; font-weight:800;
    background:linear-gradient(90deg,#a5b4fc,#e0f2fe);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; line-height:1.1;
}
.topbar-tag { font-size:0.75rem; color:#64748b; margin-top:1px; }
.topbar-pills { display:flex; gap:8px; flex-wrap:wrap; }
.pill {
    border-radius:20px; padding:3px 11px;
    font-size:0.7rem; font-weight:500; white-space:nowrap;
}
.pill-blue  { border:1px solid rgba(99,102,241,0.4); color:#a5b4fc; background:rgba(99,102,241,0.1); }
.pill-green { border:1px solid rgba(34,197,94,0.4);  color:#86efac; background:rgba(34,197,94,0.1); }
.pill-sky   { border:1px solid rgba(14,165,233,0.4); color:#7dd3fc; background:rgba(14,165,233,0.1); }
.pill-amber { border:1px solid rgba(251,191,36,0.4); color:#fde68a; background:rgba(251,191,36,0.1); }

/* ── Hero (home page) ── */
.hero {
    background: linear-gradient(135deg, #0b1628 0%, #130f2e 50%, #0b1628 100%);
    border-radius: 24px; padding: 60px 48px;
    text-align: center; margin: 28px 0 24px;
    border: 1px solid rgba(99,102,241,0.2);
    position: relative; overflow: hidden;
}
.hero::before {
    content:''; position:absolute; top:-100px; left:50%; transform:translateX(-50%);
    width:500px; height:500px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 65%);
    pointer-events:none;
}
.hero-title {
    font-size: 3.2rem; font-weight: 900; line-height: 1.1;
    background: linear-gradient(135deg, #a5b4fc 0%, #67e8f9 50%, #a5f3fc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 16px; position: relative;
}
.hero-sub {
    font-size: 1.15rem; color: #94a3b8; max-width: 560px;
    margin: 0 auto 32px; line-height: 1.6; position: relative;
}
.hero-cta {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff !important; border-radius: 12px;
    padding: 14px 36px; font-size: 1rem; font-weight: 700;
    box-shadow: 0 6px 24px rgba(99,102,241,0.45);
    cursor: pointer; border: none; transition: all 0.2s;
    text-decoration: none; position: relative;
}

/* ── Feature nav cards (home) ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin: 8px 0 32px;
}
.feature-card {
    background: #0d1624;
    border: 1px solid #1a2740;
    border-radius: 18px;
    padding: 28px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s;
    position: relative; overflow: hidden;
}
.feature-card::before {
    content:''; position:absolute; inset:0;
    background: linear-gradient(135deg, rgba(99,102,241,0.06), transparent);
    opacity:0; transition:opacity 0.25s;
}
.feature-card:hover { border-color: rgba(99,102,241,0.5); transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(99,102,241,0.15); }
.feature-card:hover::before { opacity:1; }
.fc-icon  { font-size: 2.4rem; margin-bottom: 14px; }
.fc-title { font-size: 1rem; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
.fc-desc  { font-size: 0.75rem; color: #64748b; line-height: 1.5; }
.fc-arrow {
    display: inline-block; margin-top: 14px;
    font-size: 0.75rem; color: #6366f1; font-weight: 600;
}

/* ── Stats row ── */
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:0 0 28px; }
.stat-box {
    background:#0d1624; border:1px solid #1a2740; border-radius:14px;
    padding:18px; text-align:center;
}
.stat-num { font-size:1.6rem; font-weight:800; color:#a5b4fc; }
.stat-lbl { font-size:0.72rem; color:#64748b; margin-top:3px; }

/* ── Sub-page header ── */
.page-header {
    background: linear-gradient(135deg, #0f1f40, #130f2e);
    border-radius: 16px; padding: 22px 28px;
    margin: 16px 0 24px; border: 1px solid rgba(99,102,241,0.2);
    display: flex; align-items: center; gap: 16px;
}
.page-header-icon { font-size: 2rem; }
.page-header-title { font-size: 1.2rem; font-weight: 700; color: #f1f5f9; }
.page-header-sub   { font-size: 0.8rem; color: #64748b; margin-top: 3px; }

/* ── Cards ── */
.card {
    background:#111827; border:1px solid #1f2937; border-radius:14px;
    padding:18px 22px; margin:8px 0; transition:border-color 0.2s;
}
.card-accent {
    background:linear-gradient(135deg,#13213a,#11193a);
    border:1px solid rgba(99,102,241,0.35); border-radius:16px;
    padding:20px 24px; margin:8px 0;
    box-shadow:0 2px 20px rgba(99,102,241,0.1);
}
.journey-header {
    background:linear-gradient(135deg,#0f2040,#130f2e);
    border:1px solid rgba(99,102,241,0.3); border-radius:16px;
    padding:20px 24px; margin-bottom:16px;
}
.journey-route { font-size:1.3rem; font-weight:700; color:#f1f5f9; }
.route-arrow { color:#6366f1; }
.mode-chip {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.4);
    border-radius:20px; padding:4px 14px;
    font-size:0.8rem; font-weight:600; color:#a5b4fc;
}
.rec-box {
    background:#0d1623; border:1px solid #1e3a5f;
    border-left:4px solid #6366f1; border-radius:12px;
    padding:20px 24px; color:#e2e8f0; line-height:1.8; font-size:0.92rem;
}

/* ── Badges ── */
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; }
.badge-high   { background:#450a0a; color:#fca5a5; border:1px solid #f87171; }
.badge-medium { background:#3f2006; color:#fed7aa; border:1px solid #fb923c; }
.badge-low    { background:#052e16; color:#86efac; border:1px solid #22c55e; }
.badge-none   { background:#1a2232; color:#94a3b8; border:1px solid #334155; }

/* ── Agent cards ── */
.agent-card { background:#111827; border-left:3px solid #6366f1; border-radius:10px; padding:12px 16px; margin:6px 0; }
.agent-card.success { border-left-color:#22c55e; background:#0d1f12; }
.agent-card.warning { border-left-color:#f87171; background:#1f0d0d; }
.agent-card.pii     { border-left-color:#fbbf24; background:#1f1a0d; }

/* ── Empty state ── */
.empty-state {
    text-align:center; padding:48px 24px;
    background:#0d1420; border:1px dashed #1f2f45;
    border-radius:20px; margin:12px 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background:#0a1020 !important; border-right:1px solid #1a2540; }
section[data-testid="stSidebar"] * { color:#cbd5e1 !important; }
section[data-testid="stSidebar"] .stButton>button {
    background:#111827 !important; color:#94a3b8 !important;
    border:1px solid #1f2937 !important; border-radius:9px;
    font-size:0.82rem; text-align:left; padding:8px 14px;
    transition:all 0.15s; width:100%;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background:rgba(99,102,241,0.15) !important;
    border-color:rgba(99,102,241,0.45) !important;
    color:#a5b4fc !important;
}
.nav-active button {
    background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.15)) !important;
    border-color:rgba(99,102,241,0.55) !important;
    color:#a5b4fc !important;
}

/* ── Inputs ── */
.stTextArea textarea {
    background:#0d1830 !important; color:#f1f5f9 !important;
    border:1px solid #2d3d5a !important; border-radius:10px; font-size:0.92rem !important;
}
.stTextInput input {
    background:#0d1830 !important; color:#f1f5f9 !important;
    border:1px solid #2d3d5a !important; border-radius:10px;
}

/* ── Buttons ── */
.stButton>button {
    background:linear-gradient(135deg,#6366f1,#8b5cf6);
    color:#fff !important; border:none; border-radius:10px;
    font-weight:600; padding:0.55rem 2rem; width:100%;
    font-size:0.95rem; box-shadow:0 4px 12px rgba(99,102,241,0.3); transition:all 0.2s;
}
.stButton>button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(99,102,241,0.45); }

/* ── Metrics ── */
[data-testid="stMetric"] { background:#111827; border:1px solid #1f2937; border-radius:12px; padding:14px 18px; }
[data-testid="stMetricLabel"] p { color:#64748b !important; font-size:0.75rem !important; text-transform:uppercase; letter-spacing:0.5px; }
[data-testid="stMetricValue"]   { color:#f1f5f9 !important; font-size:1.2rem !important; font-weight:700 !important; }

/* ── Misc ── */
.streamlit-expanderHeader { color:#cbd5e1 !important; background:#111827 !important; border-radius:10px; border:1px solid #1f2937 !important; }
.streamlit-expanderContent { background:#0a1020 !important; border:1px solid #1f2937; border-top:none; border-radius:0 0 10px 10px; }
.stAlert { border-radius:10px; }
hr { border-color:#1f2937 !important; }
code { background:#1e293b !important; color:#93c5fd !important; border-radius:4px; padding:2px 6px; }
.eval-bar-wrap { margin:10px 0; }
.eval-bar-label { display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; font-weight:500; margin-bottom:5px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_vector_store():
    from vectorstore import ChromaVectorStore, seed_all_collections
    from config import CHROMA_PERSIST_DIR
    store = ChromaVectorStore(persist_dir=CHROMA_PERSIST_DIR)
    seed_all_collections(store)
    return store

def go_to(page: str):
    st.session_state["page"] = page
    st.rerun()

def badge_html(level: str) -> str:
    cls = {"HIGH":"badge-high","VERY HIGH":"badge-high","MEDIUM":"badge-medium",
           "LOW":"badge-low","NONE":"badge-none"}.get(level.upper(),"badge-none")
    return f'<span class="badge {cls}">{level}</span>'

def score_color(s: float) -> str:
    return "#22c55e" if s >= 0.8 else "#f59e0b" if s >= 0.6 else "#f87171"

def mode_icon(mode: str) -> str:
    return {"metro":"🚇","bus":"🚌","bike":"🚲","walk":"🚶",
            "taxi":"🚕","cycling":"🚲","transit":"🚉"}.get(mode.lower(),"🚍")

def render_gauge(label, value, col):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value*100,
        title={"text":label,"font":{"color":"#94a3b8","size":11}},
        number={"suffix":"%","font":{"color":"#f1f5f9","size":20}},
        gauge={"axis":{"range":[0,100],"tickcolor":"#1f2937","tickfont":{"color":"#475569","size":9}},
               "bar":{"color":score_color(value),"thickness":0.7},
               "bgcolor":"#111827","bordercolor":"#1f2937","borderwidth":1,
               "steps":[{"range":[0,60],"color":"#1a0f0f"},{"range":[60,80],"color":"#1a1a0a"},{"range":[80,100],"color":"#0a1a0f"}],
               "threshold":{"line":{"color":"#6366f1","width":2},"thickness":0.75,"value":60}},
    ))
    fig.update_layout(height=155,margin=dict(l=8,r=8,t=30,b=5),
                      paper_bgcolor="#060d1f",plot_bgcolor="#060d1f",font={"color":"#e2e8f0"})
    col.plotly_chart(fig, use_container_width=True, key=f"gauge_{label}")



# ── Sidebar nav ───────────────────────────────────────────────

_CITY_QUICK_ROUTES = {
    "Metro City (Demo)": [
        ("🚇 Central → Tech Park",   "How do I get from Central Station to Tech Park?"),
        ("🎓 University → Finance",  "Best route from University Campus to Financial District"),
        ("✈️ Suburbs → Airport",     "How to travel from North Suburbs Hub to Airport Terminal?"),
        ("🏥 Medical → Old Town",    "Route from Metro Medical Center to Old Town Square"),
    ],
    "Bengaluru": [
        ("🚇 KSR Station → Electronic City",  "How do I get from KSR Bengaluru City Railway Station to Electronic City?"),
        ("💼 Indiranagar → Whitefield",        "Best route from Indiranagar to Whitefield Business District"),
        ("✈️ MG Road → KIA Airport",           "How to travel from MG Road to Kempegowda International Airport?"),
        ("🎓 Majestic → IISc Campus",          "Route from Majestic KSR to IISc Campus"),
    ],
    "Mumbai": [
        ("🚇 CST → BKC",                       "How do I get from CST Mumbai to Bandra Kurla Complex?"),
        ("✈️ Andheri → CSIA Airport",           "Best route from Andheri to CSIA T2 International Airport"),
        ("🏢 Dadar → Nariman Point",            "How to commute from Dadar Station to Nariman Point?"),
        ("🎓 CST → IIT Bombay Powai",           "Route from CST Mumbai to IIT Bombay in Powai"),
    ],
    "Delhi": [
        ("🚇 New Delhi → Connaught Place",      "How do I get from New Delhi Railway Station to Connaught Place?"),
        ("✈️ Rajiv Chowk → IGI Airport",        "Best route from Rajiv Chowk to IGI Airport Terminal 3"),
        ("🏢 Connaught Place → Cyber Hub",      "How to commute from Connaught Place to Cyber Hub Gurugram?"),
        ("🏛️ India Gate → Red Fort",            "Route from India Gate to Red Fort Delhi"),
    ],
}


def render_sidebar(use_mlflow, use_deepeval, priority, mode_pref):
    cur         = st.session_state.get("page", "home")
    saved_city  = st.session_state.get("selected_city", "Metro City (Demo)")

    with st.sidebar:
        st.markdown("""
        <div style='padding:16px 4px 12px; text-align:center;'>
            <div style='font-size:1.4rem; font-weight:800;
                background:linear-gradient(90deg,#a5b4fc,#7dd3fc);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>
                JR Commute
            </div>
            <div style='font-size:0.7rem; color:#334155; margin-top:3px;'>
                Navigate Smarter. Arrive Better.
            </div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        # ── City / Region ──
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>City / Region</div>", unsafe_allow_html=True)
        city_options = ["Metro City (Demo)", "Bengaluru", "Mumbai", "Delhi"]
        city_icons   = {"Metro City (Demo)": "🌐", "Bengaluru": "🇮🇳", "Mumbai": "🇮🇳", "Delhi": "🇮🇳"}
        selected_city = st.selectbox(
            "City",
            city_options,
            index=city_options.index(saved_city),
            format_func=lambda x: f"{city_icons[x]} {x}",
            key="sb_city",
            label_visibility="collapsed",
        )
        st.session_state["selected_city"] = selected_city

        st.divider()

        # ── Navigation ──
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>Navigation</div>", unsafe_allow_html=True)
        nav_items = [
            ("home",  "🏠  Home"),
            ("plan",  "🗺️  Plan Trip"),
            ("map",   "🏙️  City Map"),
            ("eval",  "📊  Evaluation"),
            ("pii",   "🔒  PII Guard"),
        ]
        for key, label in nav_items:
            if cur == key:
                st.markdown("<div class='nav-active'>", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                go_to(key)
            if cur == key:
                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # ── Quick Routes (city-specific) ──
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>Quick Routes</div>", unsafe_allow_html=True)
        for label, query in _CITY_QUICK_ROUTES.get(selected_city, _CITY_QUICK_ROUTES["Metro City (Demo)"]):
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state["quick_query"] = query
                go_to("plan")

        st.divider()
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>Trip Preferences</div>", unsafe_allow_html=True)
        priority  = st.selectbox("Priority", ["balanced","speed","cost","eco"],
                                  format_func=lambda x:{"balanced":"⚖️ Balanced","speed":"⚡ Fastest","cost":"💰 Cheapest","eco":"🌿 Eco-Friendly"}[x],
                                  key="sb_priority")
        mode_pref = st.selectbox("Mode", ["Any","Metro","Bus","Bike","Walk","Taxi"],
                                  format_func=lambda x:{"Any":"🔀 Any","Metro":"🚇 Metro","Bus":"🚌 Bus","Bike":"🚲 Bike","Walk":"🚶 Walk","Taxi":"🚕 Taxi"}[x],
                                  key="sb_mode")

        st.divider()
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>Integrations</div>", unsafe_allow_html=True)
        use_mlflow   = st.toggle("MLflow Tracking", value=False, key="sb_mlflow")
        use_deepeval = st.toggle("DeepEval API",    value=False, key="sb_deepeval")

        st.divider()
        st.markdown("""
        <div style='text-align:center;padding:4px 0 8px;'>
            <div style='font-size:0.65rem;color:#1e3050;line-height:1.9;'>
                Powered by <span style='color:#6366f1'>Groq · LangGraph</span><br>
                ChromaDB · LangSmith · DeepEval
            </div>
        </div>""", unsafe_allow_html=True)

    return use_mlflow, use_deepeval, priority, mode_pref, selected_city


# ── Top bar (shown on every page) ────────────────────────────

def render_topbar():
    st.markdown("""
    <div class="topbar">
        <div class="topbar-brand">
            <div class="topbar-badge">JR</div>
            <div>
                <div class="topbar-name">JR Commute</div>
                <div class="topbar-tag">Navigate Smarter. Arrive Better.</div>
            </div>
        </div>
        <div class="topbar-pills">
            <span class="pill pill-blue">⚡ Real-Time Traffic</span>
            <span class="pill pill-green">🛡️ Privacy First</span>
            <span class="pill pill-sky">🤖 9 AI Agents</span>
            <span class="pill pill-amber">✂️ Prompt Compressed</span>
        </div>
    </div>
    <div style='margin-top:8px'></div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: Home
# ══════════════════════════════════════════════════════════════

def page_home():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">Your City.<br>Your Route.<br>Your Way.</div>
        <div class="hero-sub">
            JR Commute uses 9 specialized AI agents to plan the smartest,
            safest, and fastest route through your city — in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    st.markdown("""
    <div class="stats-row">
        <div class="stat-box"><div class="stat-num">9</div><div class="stat-lbl">AI Agents</div></div>
        <div class="stat-box"><div class="stat-num">4</div><div class="stat-lbl">Quality Metrics</div></div>
        <div class="stat-box"><div class="stat-num">8</div><div class="stat-lbl">PII Types Protected</div></div>
        <div class="stat-box"><div class="stat-num">~50%</div><div class="stat-lbl">Token Compression</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Feature nav cards
    st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:14px;'>Explore</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="fc-icon">🗺️</div>
            <div class="fc-title">Plan Trip</div>
            <div class="fc-desc">Describe your commute and get a full AI-powered route plan with traffic, weather & transit insights.</div>
            <div class="fc-arrow">Go to Planner →</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open Planner", key="home_plan", use_container_width=True):
            go_to("plan")

    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="fc-icon">🏙️</div>
            <div class="fc-title">City Map</div>
            <div class="fc-desc">Explore the live city transit map, metro lines, stops, and landmarks across Metro City.</div>
            <div class="fc-arrow">Open Map →</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open Map", key="home_map", use_container_width=True):
            go_to("map")

    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="fc-icon">📊</div>
            <div class="fc-title">Evaluation</div>
            <div class="fc-desc">Review AI response quality scores across relevancy, faithfulness, completeness and safety.</div>
            <div class="fc-arrow">View Scores →</div>
        </div>""", unsafe_allow_html=True)
        if st.button("View Scores", key="home_eval", use_container_width=True):
            go_to("eval")

    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="fc-icon">🔒</div>
            <div class="fc-title">PII Guard</div>
            <div class="fc-desc">See how the Privacy Guardian automatically detects and masks sensitive personal data in every query.</div>
            <div class="fc-arrow">View Shield →</div>
        </div>""", unsafe_allow_html=True)
        if st.button("View Shield", key="home_pii", use_container_width=True):
            go_to("pii")

    # How it works
    st.divider()
    st.markdown("<div style='font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:16px;'>How It Works</div>", unsafe_allow_html=True)
    steps = [
        ("1", "#6366f1", "Describe your trip",       "Type your origin, destination, and any preferences in plain language."),
        ("2", "#0ea5e9", "9 agents collaborate",     "Parallel AI agents analyse routes, traffic, weather and transit simultaneously."),
        ("3", "#22c55e", "Get your plan",            "One clear, step-by-step recommendation with alternatives and timing."),
        ("4", "#f59e0b", "Quality guaranteed",       "Every response is automatically scored across 4 quality dimensions."),
    ]
    cols = st.columns(4, gap="medium")
    for col, (num, color, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div class="card" style='text-align:center; padding:22px 16px;'>
                <div style='width:36px;height:36px;border-radius:50%;
                            background:linear-gradient(135deg,{color}44,{color}22);
                            border:1px solid {color}66; margin:0 auto 12px;
                            display:flex;align-items:center;justify-content:center;
                            font-size:0.85rem;font-weight:800;color:{color};'>{num}</div>
                <div style='font-weight:700;font-size:0.88rem;color:#f1f5f9;margin-bottom:6px;'>{title}</div>
                <div style='font-size:0.75rem;color:#64748b;line-height:1.5;'>{desc}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: Plan Trip
# ══════════════════════════════════════════════════════════════

_LABEL = "<div style='font-size:0.72rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px;'>{}</div>"
_MINI_CARDS = """
<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:20px;'>
    <div style='background:#0d1623;border:1px solid #1a2a40;border-radius:12px;padding:14px;text-align:center;'>
        <div style='font-size:1.3rem;'>🚦</div>
        <div style='font-size:0.75rem;font-weight:600;color:#cbd5e1;margin-top:4px;'>Live Traffic</div>
        <div style='font-size:0.68rem;color:#475569;margin-top:2px;'>Rush hour aware</div>
    </div>
    <div style='background:#0d1623;border:1px solid #1a2a40;border-radius:12px;padding:14px;text-align:center;'>
        <div style='font-size:1.3rem;'>⛅</div>
        <div style='font-size:0.75rem;font-weight:600;color:#cbd5e1;margin-top:4px;'>Weather Impact</div>
        <div style='font-size:0.68rem;color:#475569;margin-top:2px;'>Mode adjustments</div>
    </div>
    <div style='background:#0d1623;border:1px solid #1a2a40;border-radius:12px;padding:14px;text-align:center;'>
        <div style='font-size:1.3rem;'>🚇</div>
        <div style='font-size:0.75rem;font-weight:600;color:#cbd5e1;margin-top:4px;'>Transit Schedules</div>
        <div style='font-size:0.68rem;color:#475569;margin-top:2px;'>Lines & frequencies</div>
    </div>
    <div style='background:#0d1623;border:1px solid #1a2a40;border-radius:12px;padding:14px;text-align:center;'>
        <div style='font-size:1.3rem;'>🔒</div>
        <div style='font-size:0.75rem;font-weight:600;color:#cbd5e1;margin-top:4px;'>Privacy Guard</div>
        <div style='font-size:0.68rem;color:#475569;margin-top:2px;'>Auto PII masking</div>
    </div>
</div>"""


def page_plan(use_mlflow, use_deepeval, priority, mode_pref):
    import re as _re

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🗺️</div>
        <div>
            <div class="page-header-title">Plan Your Trip</div>
            <div class="page-header-sub">Describe your commute and let 9 AI agents build your perfect route.</div>
        </div>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Loading knowledge base..."):
        try:
            get_vector_store()
        except Exception as e:
            st.error(f"Failed to initialize ChromaDB: {e}")
            st.stop()

    col_left, col_right = st.columns([1, 1.55], gap="large")

    # ── Left column: input form + progress placeholders ──
    with col_left:
        default_query = st.session_state.pop("quick_query", "")
        st.markdown(_LABEL.format("Describe your commute"), unsafe_allow_html=True)
        query = st.text_area("query", value=default_query, height=110, label_visibility="collapsed",
                             placeholder="e.g.  How do I get from Central Station to Tech Park during morning rush hour?")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(_LABEL.format("From"), unsafe_allow_html=True)
            origin_override = st.text_input("from", placeholder="e.g. Central Station", label_visibility="collapsed")
        with col_b:
            st.markdown(_LABEL.format("To"), unsafe_allow_html=True)
            dest_override = st.text_input("to", placeholder="e.g. Tech Park", label_visibility="collapsed")
        plan_clicked = st.button("🚀  Find My Route", use_container_width=True)
        prog_pl   = st.empty()   # progress bar
        status_pl = st.empty()   # agent status grid
        st.markdown(_MINI_CARDS, unsafe_allow_html=True)

    # ── Right column: result placeholders (populated progressively) ──
    with col_right:
        header_pl  = st.empty()
        metrics_pl = st.empty()
        rec_pl     = st.empty()
        eval_pl    = st.empty()

    # ── Helpers ──
    def _status_html(ags):
        icons = {"done": "✅", "running": "⏳", "pending": "⬜"}
        rows  = [f"{icons[s]} {n}" for n, s in ags.items()]
        return (
            "<div style='background:#0d1623;border:1px solid #1e3050;border-radius:12px;"
            "padding:12px 16px;font-size:0.78rem;line-height:2;'>"
            + " &nbsp; ".join(rows[:5]) + "<br>" + " &nbsp; ".join(rows[5:]) + "</div>"
        )

    def _journey_header_html(origin, dest, mode, traffic, weather):
        tc = "low" if traffic in ["LOW","NONE"] else "medium" if traffic == "MEDIUM" else "high"
        wc = "none" if weather in ["NONE","LOW"] else "medium" if weather == "MEDIUM" else "high"
        mode_chip = (f'<span class="mode-chip">{mode_icon(mode)} {mode.title()}</span>' if mode else "")
        return (
            f'<div class="journey-header">'
            f'<div class="journey-route">{origin} <span class="route-arrow">→</span> {dest}</div>'
            f'<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">'
            f'{mode_chip}'
            f'<span class="badge badge-{tc}">🚦 {traffic}</span>'
            f'<span class="badge badge-{wc}">⛅ {weather}</span>'
            f'</div></div>'
        )

    def _populate_result(res):
        """Fill right-column placeholders from a completed result dict."""
        if res.get("error"):
            header_pl.markdown(
                f'<div class="agent-card warning" style="padding:20px;">'
                f'<div style="font-size:1rem;font-weight:700;color:#fca5a5;margin-bottom:6px;">⛔ Request Blocked</div>'
                f'<div style="color:#94a3b8;font-size:0.88rem;">{res["error"]}</div></div>',
                unsafe_allow_html=True)
            return
        orig  = res.get("origin","—");        dst   = res.get("destination","—")
        mode  = res.get("recommended_mode","transit")
        dur   = res.get("estimated_duration","—")
        traf  = res.get("traffic_severity","—"); weat = res.get("weather_impact","—")
        header_pl.markdown(_journey_header_html(orig, dst, mode, traf, weat), unsafe_allow_html=True)
        with metrics_pl.container():
            m1, m2 = st.columns(2)
            m1.metric("Estimated Time", dur)
            m2.metric("Recommended Mode", f"{mode_icon(mode)} {mode.title()}")
        rec = res.get("recommendation","")
        rec_pl.markdown(
            _LABEL.format("Your Route Plan") +
            f'<div class="rec-box">{rec.replace(chr(10),"<br>")}</div>',
            unsafe_allow_html=True)
        scores = res.get("evaluation_scores",{})
        if scores:
            overall = scores.get("overall_score",0)
            c = score_color(overall)
            sstr = "Excellent" if overall>=0.8 else "Good" if overall>=0.6 else "Fair"
            with eval_pl.container():
                st.markdown(
                    f'<div style="background:#0d1623;border:1px solid #1a2a40;border-radius:10px;'
                    f'padding:12px 16px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;">'
                    f'<div style="font-size:0.8rem;color:#64748b;">📊 Response Quality</div>'
                    f'<div style="font-size:1rem;font-weight:700;color:{c};">{sstr} — {overall*100:.0f}%</div>'
                    f'</div>', unsafe_allow_html=True)
                if st.button("📊  View Full Evaluation", key="goto_eval_btn"):
                    go_to("eval")

    # ── Decide: run pipeline, show warning, or show last result ──
    if plan_clicked and not query.strip():
        with col_left:
            st.warning("Please describe your commute above.")

    elif plan_clicked:
        full_query = query.strip()
        if origin_override or dest_override:
            parts = []
            if origin_override: parts.append(f"from {origin_override}")
            if dest_override:   parts.append(f"to {dest_override}")
            full_query = f"{full_query} ({' '.join(parts)})"

        ags = {
            "🔒 PII Guardian":"pending","🛡️ Content Filter":"pending","🧭 Intent Parser":"pending",
            "🗺️ Route Planner":"pending","🚦 Traffic Analyst":"pending",
            "⛅ Weather Analyst":"pending","🚌 Transit Advisor":"pending",
            "⭐ Recommendation":"pending","📊 Evaluator":"pending",
        }
        ags["🔒 PII Guardian"] = "running"
        prog_pl.progress(5)
        status_pl.markdown(_status_html(ags), unsafe_allow_html=True)

        try:
            from graph import build_streaming_pipeline
            analysis_graph, rec_agent, evaluator = build_streaming_pipeline(
                use_mlflow=use_mlflow, use_langsmith=True,
                use_deepeval=use_deepeval, use_compression=True, compression_ratio=0.5,
            )
            initial_state = {
                "raw_query": full_query,
                "session_id": str(uuid.uuid4())[:8],
                "user_preferences": {"priority": priority, "mode_preference": mode_pref},
            }

            # ── Phase 1: Run analysis agents ──
            state = analysis_graph.invoke(initial_state)

            if state.get("pii_blocked") or state.get("content_blocked"):
                prog_pl.empty(); status_pl.empty()
                _populate_result(state)
                st.session_state["last_result"] = state
            else:
                for a in list(ags.keys())[:7]:
                    ags[a] = "done"
                ags["⭐ Recommendation"] = "running"
                prog_pl.progress(65)
                status_pl.markdown(_status_html(ags), unsafe_allow_html=True)

                # Show route header + "generating" placeholder immediately
                orig  = state.get("origin","—"); dst  = state.get("destination","—")
                traf  = state.get("traffic_severity","—"); weat = state.get("weather_impact","—")
                header_pl.markdown(_journey_header_html(orig, dst, "", traf, weat), unsafe_allow_html=True)
                rec_pl.markdown(
                    _LABEL.format("Your Route Plan") +
                    "<div class='rec-box'><em style='color:#475569'>✨ Generating your route plan...</em></div>",
                    unsafe_allow_html=True)

                # ── Phase 2: Stream recommendation token by token ──
                full_rec = ""
                for chunk in rec_agent.run_stream(state):
                    full_rec += chunk
                    rec_pl.markdown(
                        _LABEL.format("Your Route Plan") +
                        f'<div class="rec-box">{full_rec.replace(chr(10),"<br>")}</div>',
                        unsafe_allow_html=True)

                ags["⭐ Recommendation"] = "done"; ags["📊 Evaluator"] = "running"
                prog_pl.progress(90)
                status_pl.markdown(_status_html(ags), unsafe_allow_html=True)

                # ── Phase 3: Evaluate ──
                q_text     = state.get("masked_query", state.get("raw_query",""))
                route_docs = [r.get("summary","") for r in state.get("route_options",[])]
                trans_docs = [t.get("summary","") for t in state.get("transit_options",[])]
                eval_res   = evaluator.evaluate(q_text, full_rec, route_docs + trans_docs)

                ags["📊 Evaluator"] = "done"
                prog_pl.progress(100)
                status_pl.markdown(_status_html(ags), unsafe_allow_html=True)

                # Extract mode + duration from streamed text
                dur_m = _re.search(r"(\d+)\s*(?:to\s*\d+\s*)?(?:minutes?|mins?)", full_rec, _re.IGNORECASE)
                est_dur  = dur_m.group(0) if dur_m else "See recommendation"
                rec_mode = "transit"
                for kw in ["metro","bus","bike","walk","taxi","cycling","transit"]:
                    if kw in full_rec[:300].lower():
                        rec_mode = kw; break

                # Update header now that we have the mode
                header_pl.markdown(_journey_header_html(orig, dst, rec_mode, traf, weat), unsafe_allow_html=True)
                with metrics_pl.container():
                    m1, m2 = st.columns(2)
                    m1.metric("Estimated Time", est_dur)
                    m2.metric("Recommended Mode", f"{mode_icon(rec_mode)} {rec_mode.title()}")

                overall = eval_res.overall_score
                c = score_color(overall)
                sstr = "Excellent" if overall>=0.8 else "Good" if overall>=0.6 else "Fair"
                with eval_pl.container():
                    st.markdown(
                        f'<div style="background:#0d1623;border:1px solid #1a2a40;border-radius:10px;'
                        f'padding:12px 16px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;">'
                        f'<div style="font-size:0.8rem;color:#64748b;">📊 Response Quality</div>'
                        f'<div style="font-size:1rem;font-weight:700;color:{c};">{sstr} — {overall*100:.0f}%</div>'
                        f'</div>', unsafe_allow_html=True)
                    if st.button("📊  View Full Evaluation", key="goto_eval_btn"):
                        go_to("eval")

                result = {
                    **state,
                    "recommendation":   full_rec,
                    "recommended_mode": rec_mode,
                    "estimated_duration": est_dur,
                    "evaluation_scores": {
                        "answer_relevancy": eval_res.answer_relevancy,
                        "faithfulness":     eval_res.faithfulness,
                        "completeness":     eval_res.completeness,
                        "safety_score":     eval_res.safety_score,
                        "overall_score":    eval_res.overall_score,
                    },
                    "evaluation_summary": eval_res.feedback,
                }
                st.session_state["last_result"] = result
                time.sleep(0.6)
                prog_pl.empty(); status_pl.empty()

        except Exception as e:
            prog_pl.empty(); status_pl.empty()
            import traceback as _tb
            header_pl.markdown(
                f'<div class="agent-card warning" style="padding:20px;">'
                f'<div style="font-size:1rem;font-weight:700;color:#fca5a5;margin-bottom:6px;">⛔ Pipeline Error</div>'
                f'<div style="color:#94a3b8;font-size:0.88rem;">{e}</div></div>',
                unsafe_allow_html=True)
            rec_pl.code(_tb.format_exc())

    else:
        # Page loaded without a click — show last result or empty state
        result = st.session_state.get("last_result")
        if result:
            _populate_result(result)
        else:
            rec_pl.markdown("""
            <div class="empty-state">
                <div style='font-size:3rem;margin-bottom:12px;'>🗺️</div>
                <div style='font-size:1.05rem;font-weight:600;color:#cbd5e1;'>Your route plan will appear here</div>
                <div style='font-size:0.82rem;color:#475569;margin-top:6px;'>
                    Describe your commute on the left and hit <strong>Find My Route</strong>
                </div>
            </div>
            <div style='margin-top:16px;font-size:0.72rem;font-weight:600;color:#475569;
                        text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;'>
                Try asking JR Commute...
            </div>""" + "".join(
                f"<div style='background:#0d1623;border:1px solid #1a2a40;border-radius:10px;"
                f"padding:10px 14px;margin:6px 0;font-size:0.82rem;color:#94a3b8;'>{ex}</div>"
                for ex in [
                    "🌅 Best route during morning rush from Central Station to Tech Park?",
                    "🌧️ Should I bike or take the metro when it's raining?",
                    "💰 Cheapest way to get from University to Financial District?",
                    "⚡ Fastest route from Airport to Old Town Square?",
                ]
            ), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: City Map
# ══════════════════════════════════════════════════════════════

_CITY_FILE_MAP = {
    "Metro City (Demo)": None,          # uses legacy landmarks.json + transit_stops.json
    "Bengaluru":         "bengaluru",
    "Mumbai":            "mumbai",
    "Delhi":             "delhi",
}


def page_map(selected_city: str = "Metro City (Demo)"):
    import json
    import folium
    from streamlit_folium import st_folium

    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-icon">🏙️</div>
        <div>
            <div class="page-header-title">{selected_city} Transit Map</div>
            <div class="page-header-sub">Real interactive OpenStreetMap — landmarks, metro lines, bike share &amp; your route.</div>
        </div>
    </div>""", unsafe_allow_html=True)

    data_dir  = Path(__file__).parent.parent / "data"
    city_slug = _CITY_FILE_MAP.get(selected_city)

    try:
        if city_slug:
            with open(data_dir / "cities" / f"{city_slug}.json") as f:
                city_data = json.load(f)
            landmarks    = city_data["landmarks"]
            transit      = city_data            # metro_lines / bus_routes / bike_share_stations at top level
            map_center   = [city_data["center"]["lat"], city_data["center"]["lng"]]
            map_zoom     = city_data["zoom"]
        else:
            with open(data_dir / "landmarks.json") as f:
                landmarks = json.load(f)
            with open(data_dir / "transit_stops.json") as f:
                transit = json.load(f)
            map_center = [40.725, -73.99]
            map_zoom   = 12
    except Exception as e:
        st.error(f"Map data error: {e}")
        return

    # Controls row
    c_style, c_info = st.columns([2, 3])
    with c_style:
        map_style = st.radio("Map style", ["🌑 Dark", "🌍 Street", "⬜ Light"],
                             horizontal=True, label_visibility="collapsed", key="map_style_radio")
    tile_map = {
        "🌑 Dark":   "CartoDB dark_matter",
        "🌍 Street": "OpenStreetMap",
        "⬜ Light":  "CartoDB positron",
    }
    tiles = tile_map.get(map_style, "CartoDB dark_matter")

    result    = st.session_state.get("last_result", {})
    has_route = bool(result and not result.get("error"))

    with c_info:
        if has_route:
            origin_name = result.get("origin", "?")
            dest_name   = result.get("destination", "?")
            st.markdown(f"""
            <div style='background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
                        border-radius:10px;padding:8px 14px;font-size:0.82rem;color:#a5b4fc;margin-top:6px;'>
                🗺️ Showing your route: <strong>{origin_name}</strong> → <strong>{dest_name}</strong>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#0d1623;border:1px solid #1a2a40;border-radius:10px;
                        padding:8px 14px;font-size:0.82rem;color:#64748b;margin-top:6px;'>
                💡 Plan a trip first to see your route highlighted on the map.
            </div>""", unsafe_allow_html=True)

    # ── Build folium map ─────────────────────────────────────────
    m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=tiles, prefer_canvas=True)

    # Metro line polylines + stop circles
    line_cfg = {
        "M1": {"color": "#ef4444", "label": "Red Line"},
        "M2": {"color": "#6366f1", "label": "Blue Line"},
        "M3": {"color": "#22c55e", "label": "Green Line"},
    }
    for line in transit["metro_lines"]:
        cfg    = line_cfg[line["id"]]
        color  = cfg["color"]
        fg_ln  = folium.FeatureGroup(name=f"🚇 {cfg['label']}")
        coords = [(s["lat"], s["lng"]) for s in line["stops"]]
        folium.PolyLine(
            coords, color=color, weight=5, opacity=0.85,
            tooltip=f"{cfg['label']} · every {line['frequency_minutes']} min · {line['operating_hours']}"
        ).add_to(fg_ln)
        for stop in line["stops"]:
            folium.CircleMarker(
                [stop["lat"], stop["lng"]], radius=7,
                color="white", weight=2,
                fill=True, fill_color=color, fill_opacity=1.0,
                popup=folium.Popup(
                    f"<b>{stop['name']}</b><br>"
                    f"<span style='color:#888;font-size:11px'>{cfg['label']}</span>",
                    max_width=200
                ),
                tooltip=stop["name"]
            ).add_to(fg_ln)
        fg_ln.add_to(m)

    # Landmark markers (emoji DivIcon)
    type_colors = {
        "transit_hub":     "#3b82f6", "business_district": "#a855f7",
        "government":      "#1d4ed8", "education":         "#f97316",
        "hospital":        "#ef4444", "recreation":        "#22c55e",
        "airport":         "#06b6d4", "retail":            "#ec4899",
        "entertainment":   "#eab308", "industrial":        "#6b7280",
        "heritage":        "#d97706", "cultural":          "#14b8a6",
        "residential":     "#60a5fa",
    }
    type_emojis = {
        "transit_hub":     "🚉", "business_district": "🏢", "government":   "🏛️",
        "education":       "🎓", "hospital":          "🏥", "recreation":   "🌿",
        "airport":         "✈️", "retail":            "🛍️", "entertainment":"🎭",
        "industrial":      "🏭", "heritage":          "🏰", "cultural":     "🎨",
        "residential":     "🏠",
    }
    fg_lm = folium.FeatureGroup(name="📍 Landmarks")
    for lm in landmarks:
        color = type_colors.get(lm["type"], "#64748b")
        emoji = type_emojis.get(lm["type"], "📍")
        popup_html = (
            f"<div style='font-family:Arial;padding:2px;min-width:190px'>"
            f"<b style='font-size:13px'>{emoji} {lm['name']}</b>"
            f"<div style='color:#888;font-size:11px;margin:3px 0;text-transform:capitalize'>"
            f"{lm['type'].replace('_',' ')}</div>"
            f"<div style='font-size:11px;line-height:1.4;color:#333'>{lm['description']}</div>"
            f"</div>"
        )
        folium.Marker(
            [lm["lat"], lm["lng"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{emoji} {lm['name']}",
            icon=folium.DivIcon(
                html=(
                    f"<div style='background:{color};color:#fff;border-radius:50%;"
                    f"width:30px;height:30px;display:flex;align-items:center;"
                    f"justify-content:center;font-size:13px;"
                    f"box-shadow:0 2px 8px rgba(0,0,0,0.5);"
                    f"border:2px solid rgba(255,255,255,0.6);'>{emoji}</div>"
                ),
                icon_size=(30, 30), icon_anchor=(15, 15)
            )
        ).add_to(fg_lm)
    fg_lm.add_to(m)

    # Bike share stations (hidden by default in layer control)
    fg_bikes = folium.FeatureGroup(name="🚲 Bike Share", show=False)
    for bs in transit["bike_share_stations"]:
        folium.CircleMarker(
            [bs["lat"], bs["lng"]], radius=8,
            color="#22c55e", weight=2,
            fill=True, fill_color="#22c55e", fill_opacity=0.75,
            popup=folium.Popup(f"<b>🚲 {bs['name']}</b><br>{bs['docks']} docks", max_width=180),
            tooltip=f"🚲 {bs['name']} · {bs['docks']} docks"
        ).add_to(fg_bikes)
    fg_bikes.add_to(m)

    # Your route highlight
    if has_route:
        o_lm = next((l for l in landmarks if origin_name.lower() in l["name"].lower()), None)
        d_lm = next((l for l in landmarks if dest_name.lower()   in l["name"].lower()), None)
        if o_lm and d_lm:
            fg_rt = folium.FeatureGroup(name="🟣 Your Route")
            folium.PolyLine(
                [[o_lm["lat"], o_lm["lng"]], [d_lm["lat"], d_lm["lng"]]],
                color="#8b5cf6", weight=7, opacity=0.9, dash_array="12 6",
                tooltip=f"Your Trip: {origin_name} → {dest_name}"
            ).add_to(fg_rt)
            for lm, label, bg in [(o_lm, "▶ Start", "#22c55e"), (d_lm, "■ End", "#ef4444")]:
                folium.Marker(
                    [lm["lat"], lm["lng"]],
                    tooltip=f"{label}: {lm['name']}",
                    icon=folium.DivIcon(
                        html=(
                            f"<div style='background:{bg};color:#fff;border-radius:6px;"
                            f"padding:3px 8px;font-size:11px;font-weight:700;white-space:nowrap;"
                            f"box-shadow:0 2px 8px rgba(0,0,0,0.5);"
                            f"border:1px solid rgba(255,255,255,0.4);'>"
                            f"{label}<br><span style='font-size:9px;opacity:0.85'>{lm['name']}</span></div>"
                        ),
                        icon_size=(110, 38), icon_anchor=(55, 19)
                    )
                ).add_to(fg_rt)
            fg_rt.add_to(m)
            m.fit_bounds([
                [min(o_lm["lat"], d_lm["lat"]) - 0.015, min(o_lm["lng"], d_lm["lng"]) - 0.020],
                [max(o_lm["lat"], d_lm["lat"]) + 0.015, max(o_lm["lng"], d_lm["lng"]) + 0.020],
            ])

    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Render map
    st_folium(m, width=None, height=540, returned_objects=[], key="city_map")

    # Metro line info cards below map
    st.markdown("<div style='font-size:0.9rem;font-weight:700;color:#f1f5f9;margin:16px 0 10px;'>Metro Lines</div>", unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    for i, line in enumerate(transit["metro_lines"]):
        with cols[i]:
            color = line_cfg[line["id"]]["color"]
            stops = " → ".join(s["name"].replace(" Station","").replace(" Metro","") for s in line["stops"])
            st.markdown(f"""
            <div class="card">
                <div style='color:{color};font-weight:700;font-size:0.9rem;margin-bottom:6px;'>● {line['name']}</div>
                <div style='font-size:0.72rem;color:#64748b;margin-bottom:8px;'>
                    Every {line['frequency_minutes']} min &nbsp;·&nbsp; {line['operating_hours']}
                </div>
                <div style='font-size:0.72rem;color:#94a3b8;line-height:1.6;'>{stops}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: Evaluation
# ══════════════════════════════════════════════════════════════

def page_eval():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div>
            <div class="page-header-title">Response Quality Evaluation</div>
            <div class="page-header-sub">Every route plan is automatically scored across 4 quality dimensions.</div>
        </div>
    </div>""", unsafe_allow_html=True)

    result = st.session_state.get("last_result")
    scores = result.get("evaluation_scores",{}) if result else {}

    if scores:
        col_g1,col_g2,col_g3,col_g4 = st.columns(4)
        render_gauge("Relevancy",    scores.get("answer_relevancy",0), col_g1)
        render_gauge("Faithfulness", scores.get("faithfulness",    0), col_g2)
        render_gauge("Completeness", scores.get("completeness",    0), col_g3)
        render_gauge("Safety",       scores.get("safety_score",    0), col_g4)

        overall = scores.get("overall_score",0)
        passed  = overall >= 0.6
        c = "#22c55e" if passed else "#f87171"
        st.markdown(f"""
        <div class="card-accent" style='text-align:center;margin:16px 0;'>
            <div style='font-size:1.6rem;font-weight:800;color:{c};'>
                {'✅' if passed else '❌'} {overall*100:.1f}%
            </div>
            <div style='color:#94a3b8;margin-top:6px;font-size:0.85rem;'>
                {'PASSED — Meets quality threshold' if passed else 'NEEDS IMPROVEMENT'}
            </div>
            <div style='color:#64748b;font-size:0.8rem;margin-top:4px;'>
                {result.get('evaluation_summary','')}
            </div>
        </div>""", unsafe_allow_html=True)

        col_r, col_m = st.columns(2, gap="large")
        with col_r:
            vals = [scores.get(k,0) for k in ["answer_relevancy","faithfulness","completeness","safety_score"]]
            cats = ["Relevancy","Faithfulness","Completeness","Safety"]
            fig  = go.Figure(go.Scatterpolar(
                r=[v*100 for v in vals]+[vals[0]*100], theta=cats+[cats[0]],
                fill="toself", fillcolor="rgba(99,102,241,0.15)",
                line=dict(color="#6366f1",width=2),
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True,range=[0,100],tickfont=dict(color="#475569",size=9)),
                           angularaxis=dict(tickfont=dict(color="#cbd5e1",size=10)),bgcolor="#111827"),
                showlegend=False, paper_bgcolor="#060d1f",
                height=280, margin=dict(l=30,r=30,t=20,b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_m:
            for name, key, desc in [
                ("Answer Relevancy","answer_relevancy","Addresses the commute query"),
                ("Faithfulness",    "faithfulness",    "Grounded in retrieved data"),
                ("Completeness",    "completeness",    "Includes all key sections"),
                ("Safety Score",    "safety_score",    "Free of PII/harmful content"),
            ]:
                val = scores.get(key,0); c2 = score_color(val); pct = val*100
                st.markdown(f"""
                <div class="eval-bar-wrap">
                    <div class="eval-bar-label">
                        <span>{name}</span>
                        <span style='color:{c2};font-weight:700;'>{pct:.0f}%</span>
                    </div>
                    <div style='background:#1f2937;border-radius:6px;height:7px;overflow:hidden;'>
                        <div style='background:{c2};width:{pct:.0f}%;height:100%;border-radius:6px;'></div>
                    </div>
                    <div style='color:#475569;font-size:0.7rem;margin-top:3px;'>{desc}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Run a route query first to see evaluation scores.")
        if st.button("→  Go to Plan Trip", key="eval_goto_plan"):
            go_to("plan")
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        cols = st.columns(2, gap="medium")
        for i, (name, desc) in enumerate([
            ("📐 Answer Relevancy", "How well does the response address your specific commute query?"),
            ("🔗 Faithfulness",     "Is the answer grounded in the actual route and transit data?"),
            ("✅ Completeness",     "Does the plan include route, steps, timing, and alternatives?"),
            ("🛡️ Safety Score",     "Is the response free of PII or any harmful content?"),
        ]):
            with cols[i%2]:
                st.markdown(f"""
                <div class="card" style='margin-bottom:6px;'>
                    <div style='font-weight:700;font-size:0.88rem;color:#a5b4fc;margin-bottom:6px;'>{name}</div>
                    <div style='font-size:0.78rem;color:#64748b;'>{desc}</div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: PII Guard
# ══════════════════════════════════════════════════════════════

def page_pii():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🔒</div>
        <div>
            <div class="page-header-title">PII Privacy Guardian</div>
            <div class="page-header-sub">Every query is scanned and sanitised before reaching any AI model.</div>
        </div>
    </div>""", unsafe_allow_html=True)

    result = st.session_state.get("last_result")
    if result:
        risk     = result.get("pii_risk_level","NONE")
        entities = result.get("pii_entities",[])
        masked   = result.get("masked_query", result.get("raw_query",""))
        c1, c2   = st.columns(2)
        c1.metric("Risk Level", risk)
        c2.metric("Entities Detected", len(entities))
        if entities:
            st.markdown("**Detected & Masked:**")
            for ent in entities:
                st.markdown(f"""
                <div class="agent-card pii">
                    ⚠️ <strong>{ent.get('type','UNKNOWN')}</strong>
                    &nbsp;→&nbsp; <code>{ent.get('redacted','[REDACTED]')}</code>
                </div>""", unsafe_allow_html=True)
        st.markdown("**Processed query (after masking):**")
        st.code(masked, language=None)
    else:
        st.info("No query run yet — results will appear here after you plan a trip.")
        if st.button("→  Go to Plan Trip", key="pii_goto_plan"):
            go_to("plan")

    st.divider()
    st.markdown("#### 🧪 Test PII Detection")
    test_input = st.text_area("pii_test", key="pii_test_input", height=90, label_visibility="collapsed",
        placeholder="Try: My name is John Smith, email john@example.com, SSN 123-45-6789")
    if st.button("🔍  Scan for PII", key="pii_test_btn"):
        if test_input.strip():
            from guardrails import PIIDetector
            r = PIIDetector().detect_and_mask(test_input)
            ca, cb = st.columns(2)
            with ca:
                st.markdown("**Original**"); st.code(r.original_text)
            with cb:
                st.markdown("**After Masking**"); st.code(r.masked_text)
            rc = {"HIGH":"#f87171","MEDIUM":"#f59e0b","LOW":"#22c55e","NONE":"#475569"}.get(r.risk_level,"#475569")
            st.markdown(f"""
            <div class="card" style='margin-top:8px;'>
                Risk: <span style='color:{rc};font-weight:700;'>{r.risk_level}</span>
                &nbsp;·&nbsp; Entities: <strong>{len(r.entities)}</strong>
                &nbsp;·&nbsp; {r.pii_summary}
            </div>""", unsafe_allow_html=True)
        else:
            st.warning("Enter some text to scan.")

    st.divider()
    st.markdown("**Protected Data Types**")
    pii_types = [
        ("📧","Email",       "john@example.com → [EMAIL REDACTED]"),
        ("📞","Phone",       "555-123-4567 → [PHONE REDACTED]"),
        ("🪪","SSN",         "123-45-6789 → [SSN REDACTED]"),
        ("💳","Credit Card", "4532 1234 → [CARD REDACTED]"),
        ("🏠","Address",     "123 Main St → [ADDRESS REDACTED]"),
        ("🛂","Passport",    "A1234567 → [PASSPORT REDACTED]"),
        ("📅","Date of Birth","01/15/1990 → [DOB REDACTED]"),
        ("🌐","IP Address",  "192.168.1.1 → [IP REDACTED]"),
    ]
    cols = st.columns(4)
    for i,(icon,label,example) in enumerate(pii_types):
        with cols[i%4]:
            st.markdown(f"""
            <div class="card" style='text-align:center;padding:14px 10px;'>
                <div style='font-size:1.3rem;'>{icon}</div>
                <div style='font-size:0.78rem;font-weight:600;color:#cbd5e1;margin:5px 0 3px;'>{label}</div>
                <div style='font-size:0.65rem;color:#475569;'>{example}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════

def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    render_topbar()

    use_mlflow = use_deepeval = False
    priority   = "balanced"
    mode_pref  = "Any"
    use_mlflow, use_deepeval, priority, mode_pref, selected_city = render_sidebar(
        use_mlflow, use_deepeval, priority, mode_pref
    )

    page = st.session_state["page"]

    if page == "home":
        page_home()
    elif page == "plan":
        page_plan(use_mlflow, use_deepeval, priority, mode_pref)
    elif page == "map":
        page_map(selected_city)
    elif page == "eval":
        page_eval()
    elif page == "pii":
        page_pii()


if __name__ == "__main__":
    main()
