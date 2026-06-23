"""
Nova Stad - MLOps Dashboard
Front-end voor de FastAPI backend (zie app.py).

Ontwikkelaars: Gianni, Eduard, Wouter
"""

import io
import sys
import platform
import datetime as dt

import requests
import streamlit as st
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Configuratie
# ---------------------------------------------------------------------------
API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 10  # seconden

st.set_page_config(
    page_title="Project Nova Stad - MLOps Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Glassmorphism CSS (iOS-style liquid glass, verbeterde leesbaarheid)
# ---------------------------------------------------------------------------
GLASS_CSS = """
<style>
/* ----------  ACHTERGROND  ---------- */
.stApp {
    background: radial-gradient(circle at 15% 20%, #1e3a8a 0%, transparent 45%),
                radial-gradient(circle at 85% 80%, #6d28d9 0%, transparent 45%),
                linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    background-attachment: fixed;
    color: #f1f5f9;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ----------  GENERIEKE GLASS CARD  ---------- */
.glass-card {
    background: rgba(255, 255, 255, 0.07) !important;
    border: 1px solid rgba(255, 255, 255, 0.20) !important;
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
    margin-bottom: 1.2rem;
}

.glass-card h3 {
    margin-top: 0;
    color: #ffffff;
    font-weight: 500;
    letter-spacing: 0.3px;
}

.glass-card p, .glass-card span, .glass-card li {
    color: #e2e8f0;
}

/* ----------  HERO  ---------- */
.hero-title {
    font-size: 2.4rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #ffffff;
    margin-bottom: 0.2rem;
}
.hero-sub {
    color: #cbd5e1;
    font-size: 1rem;
    margin-bottom: 1.8rem;
}

/* ----------  METRIC  ---------- */
.metric-value {
    font-size: 2.6rem;
    font-weight: 600;
    color: #ffffff;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #94a3b8;
}

/* ----------  STATUS PILL  ---------- */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.5px;
    border: 1px solid rgba(255, 255, 255, 0.22);
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px) saturate(150%);
}
.status-online  { color: #4ade80; border-color: rgba(74, 222, 128, 0.45); }
.status-offline { color: #f87171; border-color: rgba(248, 113, 113, 0.45); }
.status-warn    { color: #facc15; border-color: rgba(250, 204, 21, 0.45); }

/* ----------  TABS  ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    padding: 6px;
    border-radius: 14px;
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #cbd5e1 !important;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(255, 255, 255, 0.14) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.22) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
}

/* ----------  KNOPPEN  ---------- */
.stButton > button {
    background: rgba(255, 255, 255, 0.10) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 12px !important;
    padding: 0.55rem 1.4rem !important;
    font-weight: 500 !important;
    backdrop-filter: blur(14px) saturate(150%);
    -webkit-backdrop-filter: blur(14px) saturate(150%);
    transition: all 0.2s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.20);
}
.stButton > button:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    border-color: rgba(255, 255, 255, 0.40) !important;
    transform: translateY(-1px);
}

/* ----------  SIDEBAR  ---------- */
section[data-testid="stSidebar"] > div {
    background: rgba(15, 23, 42, 0.55) !important;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border-right: 1px solid rgba(255, 255, 255, 0.10);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

/* ----------  EXPANDERS  ---------- */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
    overflow: hidden;
    margin-bottom: 0.8rem;
}
[data-testid="stExpander"] summary,
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #f1f5f9 !important;
    border-radius: 14px !important;
    border: none !important;
    padding: 0.7rem 1rem !important;
    font-weight: 500 !important;
}
[data-testid="stExpander"] summary:hover {
    background: rgba(255, 255, 255, 0.08) !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: rgba(15, 23, 42, 0.35) !important;
    padding: 0.8rem 1rem !important;
}

/* ----------  CODE BLOCKS  ---------- */
[data-testid="stCodeBlock"],
.stCodeBlock,
pre {
    background: rgba(8, 12, 24, 0.72) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05),
                0 4px 18px rgba(0, 0, 0, 0.30);
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stCodeBlock"] code,
pre code,
code {
    background: transparent !important;
    color: #e2e8f0 !important;
    font-family: "JetBrains Mono", "Fira Code", Consolas, monospace !important;
    font-size: 0.85rem !important;
}

/* Inline code */
:not(pre) > code {
    background: rgba(255, 255, 255, 0.10) !important;
    color: #fbbf24 !important;
    padding: 2px 6px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

/* ----------  JSON VIEWER  ---------- */
[data-testid="stJson"] {
    background: rgba(8, 12, 24, 0.72) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    padding: 0.8rem 1rem !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05),
                0 4px 18px rgba(0, 0, 0, 0.30);
}
[data-testid="stJson"] * {
    color: #e2e8f0 !important;
    font-family: "JetBrains Mono", "Fira Code", Consolas, monospace !important;
}
[data-testid="stJson"] .object-key {
    color: #93c5fd !important;
}
[data-testid="stJson"] .string-value {
    color: #86efac !important;
}
[data-testid="stJson"] .number-value {
    color: #fbbf24 !important;
}
[data-testid="stJson"] .boolean-value {
    color: #f472b6 !important;
}

/* ----------  INPUTS  ---------- */
.stNumberInput input,
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(14px) saturate(150%);
    -webkit-backdrop-filter: blur(14px) saturate(150%);
}
.stNumberInput input:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 0 0 2px rgba(147, 197, 253, 0.15) !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] {
    background: transparent !important;
}
.stSlider [data-baseweb="slider"] > div > div {
    background: rgba(255, 255, 255, 0.18) !important;
}

/* ----------  FILE UPLOADER  ---------- */
[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1.5px dashed rgba(255, 255, 255, 0.28) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    padding: 1rem !important;
}
[data-testid="stFileUploader"] section:hover {
    background: rgba(255, 255, 255, 0.10) !important;
    border-color: rgba(255, 255, 255, 0.45) !important;
}
[data-testid="stFileUploader"] button {
    background: rgba(255, 255, 255, 0.12) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.22) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span {
    color: #cbd5e1 !important;
}

/* ----------  ALERTS / INFO / WARNING  ---------- */
[data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.07) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
    color: #f1f5f9 !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
}
[data-testid="stAlert"] * { color: #f1f5f9 !important; }

/* ----------  CAPTION / SMALL  ---------- */
.stCaption, small, .caption {
    color: #94a3b8 !important;
}

/* ----------  DETECTIE-LIJST  ---------- */
.det-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    margin: 8px 0;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 12px;
    backdrop-filter: blur(14px) saturate(150%);
    -webkit-backdrop-filter: blur(14px) saturate(150%);
}
.det-label { color: #ffffff; font-weight: 500; text-transform: capitalize; }
.det-score { color: #93c5fd; font-variant-numeric: tabular-nums; }

/* ----------  DIVIDER  ---------- */
hr {
    border-color: rgba(255, 255, 255, 0.12) !important;
}

/* ----------  FOOTER  ---------- */
.app-footer {
    text-align: center;
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 2rem;
    letter-spacing: 0.4px;
}
</style>
"""
st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# API-helpers
# ---------------------------------------------------------------------------
def api_get(path: str, **kwargs):
    """GET-request met nette foutafhandeling."""
    try:
        r = requests.get(f"{API_BASE_URL}{path}", timeout=REQUEST_TIMEOUT, **kwargs)
        return r.status_code, r.json(), None
    except requests.exceptions.ConnectionError:
        return None, None, "ConnectionError"
    except requests.exceptions.Timeout:
        return None, None, "Timeout"
    except Exception as exc:
        return None, None, str(exc)


def api_post(path: str, files=None):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", files=files, timeout=REQUEST_TIMEOUT * 3)
        return r.status_code, r.json(), None
    except requests.exceptions.ConnectionError:
        return None, None, "ConnectionError"
    except requests.exceptions.Timeout:
        return None, None, "Timeout"
    except Exception as exc:
        return None, None, str(exc)


def fetch_health():
    return api_get("/health")


# ---------------------------------------------------------------------------
# Sidebar - technische schil voor de docent
# ---------------------------------------------------------------------------
with st.sidebar:
    # Voeg de QR code bovenaan toe
    try:
        st.image("qr-code nova-stad.svg", use_container_width=True)
    except Exception:
        pass # Dit voorkomt een harde crash mocht het bestand ontbreken

    st.markdown("### Project Nova Stad")
    st.caption("MLOps Dashboard - technische schil")

    status_code, health_json, health_err = fetch_health()
    if health_err is None and status_code == 200:
        pill = '<span class="status-pill status-online">API ONLINE</span>'
        backend_ok = True
    elif health_err == "ConnectionError":
        pill = '<span class="status-pill status-offline">API OFFLINE</span>'
        backend_ok = False
    else:
        pill = '<span class="status-pill status-warn">API DEGRADED</span>'
        backend_ok = False
    st.markdown(pill, unsafe_allow_html=True)
    st.markdown(f"<small>Endpoint: <code>{API_BASE_URL}</code></small>", unsafe_allow_html=True)

    if not backend_ok:
        st.warning(
            "Geen verbinding met de FastAPI backend. "
            "Start de server met:\n\n`uvicorn app:app --reload`"
        )

    st.divider()

    with st.expander("API Health Response", expanded=False):
        if backend_ok:
            st.json(health_json)
        else:
            st.code(f"Fout: {health_err or 'onbekend'}", language="text")

    with st.expander("Systeeminformatie", expanded=False):
        st.markdown(
            f"""
            - **Python**: {sys.version.split()[0]}
            - **Platform**: {platform.system()} {platform.release()}
            - **Machine**: {platform.machine()}
            - **Streamlit**: {st.__version__}
            - **Requests**: {requests.__version__}
            - **Sessie gestart**: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
        )

    with st.expander("MLOps Architectuur", expanded=False):
        st.markdown(
            """
            - **Cloud-model**: RandomForestRegressor (sklearn) - voorspelt
              verkeersintensiteit op basis van het uur van de dag.
            - **Edge-model**: SSDLite320 MobileNetV3 (torchvision) -
              objectdetectie op afbeeldingen.
            - **Backend**: FastAPI + Uvicorn.
            - **Front-end**: Streamlit met glassmorphism UI.
            - **Communicatie**: REST/JSON over HTTP.
            """
        )

    with st.expander("Ontwikkelaars", expanded=False):
        st.markdown(
            """
            - **Gianni**
            - **Eduard**
            - **Wouter**
            """
        )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">Project Nova Stad</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Geintegreerd MLOps-dashboard voor cloud-voorspellingen en edge-detectie.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_cloud, tab_edge = st.tabs(["Cloud - Verkeersvoorspelling", "Edge - Objectdetectie"])

# ===========================================================================
# CLOUD TAB
# ===========================================================================
with tab_cloud:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Invoer")
        st.write(
            "Selecteer een uur van de dag (0 - 23) om de verwachte "
            "verkeersintensiteit op te vragen bij het cloud-model."
        )
        uur = st.slider("Uur van de dag", min_value=0, max_value=23, value=8, step=1)
        predict_clicked = st.button("Voorspelling ophalen", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_out:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Resultaat")

        if predict_clicked:
            sc, data, err = api_get("/cloud/predict_traffic", params={"hour": uur})
            if err == "ConnectionError":
                st.error("Geen verbinding met de backend. Controleer of FastAPI draait.")
                data = None
            elif err is not None:
                st.error(f"Onverwachte fout: {err}")
                data = None
            elif sc != 200:
                st.error(f"API gaf statuscode {sc} terug.")
                data = None
            else:
                pred = data.get("predicted_traffic_volume", 0.0)
                st.markdown('<div class="metric-label">Verwachte intensiteit</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-value">{pred:.1f}</div>'
                    if isinstance(pred, (int, float))
                    else f'<div class="metric-value">{pred}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Voorspeld voor uur {uur}:00")
            st.session_state["cloud_last"] = data
        else:
            st.caption("Nog geen voorspelling opgevraagd.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Ruwe JSON-response (Cloud)"):
        if st.session_state.get("cloud_last"):
            st.json(st.session_state["cloud_last"])
        else:
            st.caption("Geen response beschikbaar.")

# ===========================================================================
# EDGE TAB
# ===========================================================================
with tab_edge:
    col_up, col_res = st.columns([1, 1], gap="large")

    with col_up:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Afbeelding uploaden")
        st.write(
            "Upload een JPG- of PNG-bestand. Het edge-model detecteert "
            "voertuigen en personen via SSDLite320 MobileNetV3."
        )
        uploaded = st.file_uploader(
            "Selecteer een afbeelding",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        detect_clicked = st.button("Detectie uitvoeren", use_container_width=True, disabled=uploaded is None)

        if uploaded is not None:
            try:
                img = Image.open(uploaded)
                st.image(img, caption="Geuploade afbeelding", use_container_width=True)
            except Exception as exc:
                st.error(f"Kan afbeelding niet openen: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_res:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Detectieresultaten")

        if detect_clicked and uploaded is not None:
            uploaded.seek(0)
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "image/jpeg")}
            sc, data, err = api_post("/edge/detect_objects", files=files)

            if err == "ConnectionError":
                st.error("Geen verbinding met de backend. Controleer of FastAPI draait.")
                data = None
            elif err is not None:
                st.error(f"Onverwachte fout: {err}")
                data = None
            elif sc != 200:
                st.error(f"API gaf statuscode {sc} terug.")
                data = None
            else:
                detections = data.get("results", {}).get("detections", [])
                total = len(detections)

                st.markdown('<div class="metric-label">Totaal aantal detecties</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{total}</div>', unsafe_allow_html=True)

                if total > 0:
                    # --- NIEUW: Teken de bounding boxes op de afbeelding ---
                    # We maken een kopie van de originele afbeelding
                    img_with_boxes = img.copy()
                    draw = ImageDraw.Draw(img_with_boxes)
                    
                    # Definieer kleuren voor de meest voorkomende objecten
                    color_map = {
                        "car": "#3b82f6",      # Blauw
                        "person": "#ef4444",   # Rood
                        "bus": "#eab308",      # Geel
                        "truck": "#f97316",    # Oranje
                        "bicycle": "#22c55e"   # Groen
                    }
                    
                    for det in detections:
                        lbl = det.get("object", "onbekend")
                        score = float(det.get("score", 0.0))
                        box = det.get("box")
                        
                        # Als we coördinaten hebben gekregen van de backend
                        if box and len(box) == 4:
                            x_min, y_min, x_max, y_max = box
                            # Bepaal de kleur (standaard grijs/wit als ie niet in de color_map zit)
                            box_color = color_map.get(lbl, "#f1f5f9")
                            
                            # Teken het kader (width is de dikte van de lijn)
                            draw.rectangle([x_min, y_min, x_max, y_max], outline=box_color, width=4)
                            # Teken een klein tekstvakje met het label en de score
                            draw.text((x_min + 5, y_min + 5), f"{lbl} ({score:.2f})", fill=box_color)

                    # Toon de bewerkte foto met kaders direct in het resultaten-venster
                    st.markdown("### Visuele Detectie")
                    st.image(img_with_boxes, use_container_width=True)
                    st.divider()
                    # -----------------------------------------------------

                    # Hier start je originele code voor 'Aggregatie per klasse' weer:
                    agg = {}
                    for det in detections:
                        lbl = det.get("object", "onbekend")
                        score = det.get("score") or det.get("confidence") or 0.0
                        agg.setdefault(lbl, []).append(float(score))

                    st.markdown("<br/>", unsafe_allow_html=True)
                    for lbl, scores in sorted(agg.items(), key=lambda x: -len(x[1])):
                        avg = sum(scores) / len(scores)
                        st.markdown(
                            f'<div class="det-row">'
                            f'<span class="det-label">{lbl} ({len(scores)}x)</span>'
                            f'<span class="det-score">avg {avg:.2f}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("Geen objecten gedetecteerd.")
            st.session_state["edge_last"] = data
        else:
            st.caption("Upload een afbeelding en start de detectie.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Ruwe JSON-response (Edge)"):
        if st.session_state.get("edge_last"):
            st.json(st.session_state["edge_last"])
        else:
            st.caption("Geen response beschikbaar.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="app-footer">Project Nova Stad - MLOps Dashboard - Gianni, Eduard, Wouter</div>',
    unsafe_allow_html=True,
)
