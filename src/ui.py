from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st


PAGE_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

* { box-sizing: border-box; }

.stApp {
    background: radial-gradient(ellipse at top, #1a1508 0%, #0D0D12 50%, #080810 100%);
    min-height: 100vh;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; max-width: 960px; }

p, div, label, span {
    font-family: 'Crimson Text', serif !important;
    color: #E8DFC8 !important;
    font-size: 1.1rem;
}

.streamlit-expanderHeader {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.2em !important;
    color: #C9A84C !important;
    background: transparent !important;
    padding: 0.8rem 0 !important;
}

.streamlit-expanderHeader p {
    font-size: 0.75rem !important;
    margin: 0 !important;
    line-height: 1 !important;
}

.streamlit-expanderContent {
    border-left: 1px solid rgba(201,168,76,0.15) !important;
    padding-left: 1rem !important;
}

div[data-testid='stExpander'] div {
    font-size: unset;
}

.stTextInput input, .stSelectbox select, .stDateInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(201,168,76,0.05) !important;
    border: 1px solid rgba(201,168,76,0.25) !important;
    border-radius: 2px !important;
    color: #E8DFC8 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.1rem !important;
}

label {
    color: #C9A84C !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 4px 4px 0 0;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
    color: rgba(232, 223, 200, 0.5);
    font-family: 'Cinzel', serif;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(201, 168, 76, 0.05);
    color: #C9A84C !important;
    border-bottom: 2px solid #C9A84C !important;
}

.stButton > button {
    background: linear-gradient(135deg, #C9A84C, #8B6914) !important;
    color: #0D0D12 !important;
    font-family: 'Cinzel', serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.2em !important;
    border: none !important;
    padding: 0.75rem 3rem !important;
    border-radius: 1px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #E8C96A, #C9A84C) !important;
    box-shadow: 0 0 20px rgba(201,168,76,0.4) !important;
}

div[data-testid='stMetric'] {
    background: rgba(201,168,76,0.05);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 2px;
    padding: 1rem 1.5rem;
    text-align: center;
}

div[data-testid='stMetricLabel'] p {
    font-family: 'Cinzel', serif !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em !important;
    color: rgba(201,168,76,0.6) !important;
    text-transform: uppercase;
}

div[data-testid='stMetricValue'] {
    font-family: 'Cinzel', serif !important;
    color: #C9A84C !important;
    font-size: 1.8rem !important;
}

.sec-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0 1rem 0;
}

.sec-line {
    flex: 1;
    height: 1px;
    background: rgba(201, 168, 76, 0.2);
}

.sec-text {
    font-family: 'Cinzel', serif;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: #C9A84C;
    white-space: nowrap;
}
</style>
"""

def configure_page() -> None:
    st.set_page_config(page_title="PRASNA TANTRA", page_icon="*", layout="centered")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)


def init_session_state() -> None:
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "nlp_parsed" not in st.session_state:
        st.session_state.nlp_parsed = None
    if "show_details" not in st.session_state:
        st.session_state["show_details"] = False


def section_header(title: str) -> None:
    st.markdown(
        f"""
        <div class='sec-header'>
            <div class='sec-line'></div>
            <div class='sec-text'>{title.upper()}</div>
            <div class='sec-line'></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div style='text-align:center; padding: 3rem 0 1rem 0;'>
            <div style='font-family:Cinzel,serif; font-size:0.7rem; letter-spacing:0.4em;
                 color:rgba(201,168,76,0.5); margin-bottom:1rem;'>
                VEDIC HORARY ASTROLOGY
            </div>
            <div style='font-family:Cinzel,serif; font-size:3.5rem; font-weight:700;
                 color:#C9A84C; letter-spacing:0.1em;
                 text-shadow: 0 0 60px rgba(201,168,76,0.25);'>
                PRASNA TANTRA
            </div>
            <div style='font-family:Cinzel,serif; font-size:0.65rem; letter-spacing:0.35em;
                 color:rgba(232,223,200,0.5); margin-top:0.5rem;'>
                SRI NEELAKANTA | 1567 AD
            </div>
            <div style='width:60px; height:1px; background:#C9A84C;
                 margin: 1.5rem auto; opacity:0.4;'></div>
            <div style='font-family:Crimson Text,serif; font-style:italic; font-size:1.1rem;
                 color:rgba(232,223,200,0.6); max-width:500px; margin:0 auto;'>
                Cast a chart for the moment your question arises.<br>The heavens hold the answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_form() -> dict:
    with st.form(key="prasna_form"):
        col1, col2 = st.columns(2)
        with col1:
            city_input = st.text_input("City of Query", value="New Delhi")
            manual_coords = st.checkbox("Manual Coordinates")
            lat_input = lon_input = None
            if manual_coords:
                lat_input = st.number_input("Latitude", value=28.6139, format="%.4f")
                lon_input = st.number_input("Longitude", value=77.2090, format="%.4f")
        with col2:
            date_query = st.date_input("Date", value=datetime.date.today())
            time_query = st.text_input("Time (HH:MM:SS)", value="12:00:00")

        st.markdown("<br>", unsafe_allow_html=True)
        user_question = st.text_area(
            "Write your question",
            placeholder="e.g. Will I get married? Will I recover from illness? Will I get the job?",
            height=120,
            max_chars=300,
        )
        st.markdown(
            "<div style='font-family:Crimson Text,serif; font-style:italic; font-size:0.9rem; color:rgba(232,223,200,0.6); margin-top:0.5rem;'>"
            "Prasna Tantra prefers one sincere, clearly written question. The app will identify the relevant house from your wording."
            "</div>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Cast the Chart")

    return {
        "submitted": submitted,
        "city_input": city_input,
        "manual_coords": manual_coords,
        "lat_input": lat_input,
        "lon_input": lon_input,
        "date_query": date_query,
        "time_query": time_query,
        "user_question": user_question,
    }


def render_sincerity_gate(sinc: dict) -> None:
    if not sinc:
        return

    verdict = sinc.get("verdict", "neutral")
    message = sinc.get("message", "")
    insincere_rules = sinc.get("matched_insincere_rules", [])
    sincere_rules = sinc.get("matched_sincere_rules", [])

    if verdict == "declined":
        st.markdown(
            f"""
            <div style='border: 1px solid #8B3A3A; border-left: 4px solid #8B3A3A;
                 background: rgba(139,58,58,0.08); padding: 2rem; margin: 2rem 0;
                 text-align: center;'>
                <div style='font-family:Cinzel,serif; font-size:0.7rem; letter-spacing:0.3em;
                     color:#8B3A3A; margin-bottom:1rem;'>READING DECLINED</div>
                <div style='font-family:Crimson Text,serif; font-size:1.2rem; color:#E8DFC8;
                     font-style:italic; line-height:1.8;'>
                    {message}<br><br>
                    <span style='font-size:0.95rem; color:rgba(232,223,200,0.5);'>
                    "Any questions posed light-heartedly or with mischievous intention
                    should be dismissed by the astrologer."
                    </span>
                </div>
                <div style='margin-top:1.5rem; font-family:Cinzel,serif; font-size:0.6rem;
                     letter-spacing:0.2em; color:rgba(139,58,58,0.6);'>
                    Matched insincere rules: {', '.join(insincere_rules) if insincere_rules else 'None'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    label_map = {
        "confirmed": ("SINCERE INTENT CONFIRMED", "#4A7C59"),
        "caution": ("MIXED SIGNALS - Proceed carefully", "#C9A84C"),
        "neutral": ("NEUTRAL CHART - Proceeding", "#C9A84C"),
    }
    label, color = label_map.get(verdict, label_map["neutral"])
    st.markdown(
        f"""
        <div style='border-left:3px solid {color}; padding:1rem 1.5rem;
             background:rgba(0,0,0,0.2); margin-bottom:1rem;'>
            <div style='font-family:Cinzel,serif; font-size:0.6rem; letter-spacing:0.25em;
                 color:{color}; margin-bottom:0.5rem;'>{label}</div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem;
                 color:#E8DFC8; font-style:italic;'>{message}</div>
            <div style='margin-top:0.5rem; font-family:Cinzel,serif; font-size:0.55rem;
                 letter-spacing:0.15em; color:rgba(232,223,200,0.4);'>
                Sincere indicators: {', '.join(sincere_rules) if sincere_rules else 'None'} | 
                Insincere indicators: {', '.join(insincere_rules) if insincere_rules else 'None'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_parsed_question_box(parsed: dict) -> None:
    confidence_color = "#4A7C59" if parsed["confidence"] == "high" else "#C9A84C" if parsed["confidence"] == "medium" else "#8B3A3A"
    reasoning_intro = parsed.get("reasoning", "").split("(")[0].strip()
    st.markdown(
        f"""
        <div style='border:1px solid rgba(201,168,76,0.2); border-left:3px solid #C9A84C;
             background:rgba(201,168,76,0.04); padding:1.2rem 1.5rem; margin:1rem 0;'>
            <div style='font-family:Cinzel,serif; font-size:0.55rem; letter-spacing:0.25em;
                 color:rgba(201,168,76,0.6); margin-bottom:0.5rem;'>QUESTION INTERPRETED</div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8;'>
                <b>Your question:</b> "{parsed.get('rephrased', '')}"
            </div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8; margin-top:0.3rem;'>
                <b>Mapped to:</b> House {parsed.get('query_house', '?')} -
                <span style='color:#C9A84C;'>{reasoning_intro}</span>
            </div>
            <div style='font-family:Cinzel,serif; font-size:0.55rem; letter-spacing:0.15em;
                 color:{confidence_color}; margin-top:0.5rem;'>
                Confidence: {parsed.get('confidence', 'unknown').upper()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_answer_block(res: dict) -> None:
    judg = res.get("house_judgment", {})
    perf = res.get("performance", {})
    positions = res.get("positions", {})
    tim = res.get("timing_estimate", {})
    lagna_lord_name = judg.get("lagna_lord", "Unknown")
    lagna_lord = positions.get(lagna_lord_name)
    karyesh_name = judg.get("karyesh", "Unknown")
    karyesh = positions.get(karyesh_name)
    perfection = "Ithasala" if judg.get("ithasala_present") else "Easarapha" if judg.get("easarapha_present") else "None"

    st.markdown("<hr style='border: none; border-top: 1px solid rgba(201,168,76,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    section_header("The Answer")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Success Chance", f"{judg.get('karyasiddhi_percent', 0)}%")
    with m2:
        st.metric("House Vitality", judg.get("house_vitality", "Unknown"))
    with m3:
        st.metric("Perfection", perfection)

    specific_verdict = judg.get("specific_verdict", "")
    specific_factors = judg.get("specific_factors", [])
    query_time_meaning = judg.get("query_time_meaning", "")
    interpretation = judg.get("interpretation", "Consult a scholar.")
    primary_timing = tim.get("most_likely", {})

    content_html = f"<b>Core judgment:</b> {interpretation}"
    if specific_verdict and "General house judgment" not in specific_verdict:
        content_html += f"<br><br><b>Topic-specific reading:</b> {specific_verdict}"
    elif specific_verdict:
        content_html += f"<br><br><b>Topic-specific reading:</b> {specific_verdict}"

    st.markdown(
        f"""
        <div style='border:1px solid rgba(201,168,76,0.3); border-left: 3px solid #C9A84C;
             background:rgba(201,168,76,0.04); padding:1.2rem 1.5rem; margin:1rem 0;
             font-family:Crimson Text,serif; font-size:1.15rem; color:#E8DFC8; line-height:1.6;'>
            {content_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    basis_html = f"""
    <div style='border:1px solid rgba(201,168,76,0.18); background:rgba(255,255,255,0.02);
         padding:1rem 1.2rem; margin:0.8rem 0 1rem 0;'>
        <div style='font-family:Cinzel,serif; font-size:0.58rem; letter-spacing:0.2em; color:#C9A84C; margin-bottom:0.7rem;'>
            READING BASIS
        </div>
        <div><b>Lagna:</b> {judg.get('lagna_sign', 'Unknown')} | <b>Lagna lord:</b> {lagna_lord_name} in House {lagna_lord.get('house', '?') if lagna_lord else '?'}</div>
        <div><b>Moon:</b> {'Unafflicted' if judg.get('moon_unafflicted') else 'Afflicted'} | <b>Phase:</b> {judg.get('moon_phase', 'unknown').capitalize()}</div>
        <div><b>Query house:</b> {judg.get('query_house', '?')} ({judg.get('query_house_sign', 'Unknown')}) | <b>Significator:</b> {karyesh_name} in House {karyesh.get('house', '?') if karyesh else '?'}</div>
        <div><b>Tajaka:</b> {perfection}{' + Kamboola' if judg.get('kamboola_present') else ''}</div>
    </div>
    """
    st.markdown(basis_html, unsafe_allow_html=True)

    if specific_factors:
        st.markdown("<h5 style='color: #E2E2E2; margin-top: 15px;'>Combinations Detected</h5>", unsafe_allow_html=True)
        for factor in specific_factors:
            st.markdown(f"- <span style='color:rgba(232,223,200,0.85);'>{factor}</span>", unsafe_allow_html=True)

    if query_time_meaning:
        st.markdown(
            f"<div style='font-family:Crimson Text,serif; font-style:italic; font-size:0.95rem; color:rgba(232,223,200,0.5); margin-top:0.8rem;'>{query_time_meaning}</div>",
            unsafe_allow_html=True,
        )
    if primary_timing and primary_timing.get("value") is not None and judg.get("ithasala_present"):
        st.markdown(
            f"<div style='font-family:Crimson Text,serif; font-size:1rem; color:#E8DFC8; margin-top:0.5rem;'><b>Primary timing:</b> {primary_timing.get('value')} {primary_timing.get('unit')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        btn_label = "HIDE ASTROLOGICAL DETAILS" if st.session_state["show_details"] else "VIEW ASTROLOGICAL DETAILS"
        if st.button(btn_label, key="toggle_details"):
            st.session_state["show_details"] = not st.session_state["show_details"]
            st.rerun()

    if st.session_state["show_details"]:
        render_details_panel(res)

    st.markdown(
        f"""
        <div style='margin-top:2rem; font-family:Cinzel,serif; font-size:0.6rem; letter-spacing:0.2em; color:rgba(201,168,76,0.3);'>
            COMPUTED IN {perf.get('total_ms', '?')}MS | PRASNA TANTRA ENGINE
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_details_panel(res: dict) -> None:
    judg = res.get("house_judgment", {})
    yog = res.get("yogas", {})
    avas = res.get("avasthas", {})
    tim = res.get("timing_estimate", {})
    positions = res.get("positions", {})
    karyesh_name = judg.get("karyesh", "Unknown")
    karyesh = positions.get(karyesh_name, {})

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    section_header("Reading Basis")
    m_l1, m_l2, m_l3 = st.columns(3)
    with m_l1:
        st.metric("Lagna", f"{judg.get('lagna_sign', 'Unknown')} (House 1)")
    with m_l2:
        st.metric("Moon", "Unafflicted" if judg.get("moon_unafflicted") else "Afflicted")
    with m_l3:
        st.metric("Significator", f"{karyesh_name} / House {karyesh.get('house', '?')}")

    lagna_factors = []
    lagna_factors.append("Lagna lord aspects the Ascendant - favourable" if judg.get("lagna_lord_aspects_lagna") else "Lagna lord does not aspect the Ascendant - weakness")
    lagna_factors.append("Benefic planet occupies the Ascendant - strong positive" if judg.get("benefic_in_lagna") else "A benefic planet aspects the Ascendant - strengthens query" if judg.get("benefic_aspects_lagna") else "No benefic aspects the Ascendant")
    lagna_factors.append("Moon = seed, Lagna = flower, query house = outcome framework applied")
    lagna_factors.append(f"Rising type: {judg.get('lagna_rise_type', 'unknown').capitalize()}")
    if judg.get("moon_supports_query"):
        lagna_factors.append("Moon supports the query significator - helpful secondary testimony")

    for factor in lagna_factors:
        color = "#4A7C59" if "no " not in factor.lower() and "weakness" not in factor.lower() and "afflicted" not in factor.lower() else "#8B3A3A"
        st.markdown(f"<div style='color:{color};'>{factor}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    section_header("Planet States")
    if avas:
        df_data = pd.DataFrame(
            [{"Planet": p, "State": d.get("avastha", "").capitalize(), "Strength": d.get("strength", "").capitalize()} for p, d in avas.items()]
        )
        st.dataframe(df_data, hide_index=True, use_container_width=True)

    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    section_header("Tajaka Yogas")
    for label, key in [("Applying (Ithasala)", "ithasala"), ("Separating (Easarapha)", "easarapha"), ("Translation (Nakta)", "naktha"), ("Translation (Yamaya)", "yamaya"), ("Moon Reinforcement (Kamboola)", "kamboola")]:
        items = yog.get(key, [])
        if items:
            st.markdown(f"**{label}:**")
            for item in items:
                if key in {"ithasala", "easarapha"}:
                    st.write(f"- {item['faster_planet']} + {item['slower_planet']} ({item['exact_aspect_deg']} degrees)")
                elif key in {"naktha", "yamaya"}:
                    pair = item.get("planet_pair", ("?", "?"))
                    st.write(f"- {pair[0]} + {pair[1]} via {item.get('mediator', '?')}")
                else:
                    pair = item.get("ithasala_pair", ("?", "?"))
                    st.write(f"- {pair[0]} + {pair[1]} reinforced by Moon")

    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    section_header("Timing Details")
    if tim:
        if tim.get("error"):
            st.markdown(f"*Timing could not be resolved cleanly: {tim['error']}*")
        else:
            st.markdown("**Primary method:** degree gap plus sign quality")
            st.markdown(f"**Calculated Time:** {tim.get('most_likely', {}).get('value', '?')} {tim.get('most_likely', {}).get('unit', '')}")
            st.markdown(f"*{tim.get('timing_note', '')}*")
            if tim.get("method_2") and tim.get("method_3"):
                st.markdown(f"Secondary classical estimates: Method 2 = {tim['method_2']['value']} {tim['method_2']['unit']}, Method 3 = {tim['method_3']['value']} {tim['method_3']['unit']}")

    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    section_header("Computational Summary")
    st.markdown(f"<div style='font-style:italic;'>{res.get('summary', '')}</div>", unsafe_allow_html=True)
