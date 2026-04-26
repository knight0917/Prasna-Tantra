from __future__ import annotations

import datetime

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


def _perfection_label(judg: dict) -> str:
    if judg.get("ithasala_present"):
        quality = judg.get("ithasala_quality")
        if quality == "obstructed":
            return "Ithasala with Obstruction"
        return "Ithasala"
    if judg.get("hostile_applying_present"):
        return "Hostile Application"
    if judg.get("easarapha_present"):
        return "Easarapha"
    return "None"


def _headline_answer(judg: dict) -> str:
    for text in (judg.get("specific_verdict", ""), judg.get("interpretation", "")):
        upper = text.upper()
        if upper.startswith("YES, WITH EFFORT"):
            return "YES, WITH EFFORT"
        if upper.startswith("YES"):
            return "YES"
        if upper.startswith("NO"):
            return "NO"
        if upper.startswith("UNCLEAR"):
            return "UNCLEAR"
        if upper.startswith("CRITICAL"):
            return "CRITICAL"
    return "UNCLEAR"


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
        "neutral": ("NEUTRAL CHART - Proceed with caution", "#C9A84C"),
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
    reasoning_intro = parsed.get("reasoning", "").split("(")[0].strip()
    st.markdown(
        f"""
        <div style='border:1px solid rgba(201,168,76,0.2); border-left:3px solid #C9A84C;
             background:rgba(201,168,76,0.04); padding:1.2rem 1.5rem; margin:1rem 0;'>
            <div style='font-family:Cinzel,serif; font-size:0.55rem; letter-spacing:0.25em;
                 color:rgba(201,168,76,0.6); margin-bottom:0.5rem;'>QUESTION</div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8;'>
                "{parsed.get('rephrased', '')}"
            </div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8; margin-top:0.3rem;'>
                <b>House concerned:</b> House {parsed.get('query_house', '?')} -
                <span style='color:#C9A84C;'>{reasoning_intro}</span>
            </div>
            {f"<div style='font-family:Crimson Text,serif; font-size:0.95rem; color:rgba(232,223,200,0.68); margin-top:0.3rem;'><b>Derived house:</b> {parsed.get('derived_from')}</div>" if parsed.get('derived_house_used') and parsed.get('derived_from') else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_answer_block(res: dict) -> None:
    judg = res.get("house_judgment", {})
    positions = res.get("positions", {})
    tim = res.get("timing_estimate", {})
    lagna_lord_name = judg.get("lagna_lord", "Unknown")
    lagna_lord = positions.get(lagna_lord_name)
    karyesh_name = judg.get("karyesh", "Unknown")
    karyesh = positions.get(karyesh_name)
    perfection = _perfection_label(judg)
    headline = _headline_answer(judg)

    st.markdown("<hr style='border: none; border-top: 1px solid rgba(201,168,76,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    section_header("Judgment")

    specific_verdict = judg.get("specific_verdict", "")
    specific_factors = judg.get("specific_factors", [])
    source_rules = judg.get("source_rules", [])
    query_time_meaning = judg.get("query_time_meaning", "")
    interpretation = judg.get("interpretation", "Consult a scholar.")
    primary_timing = tim.get("most_likely", {})

    content_html = f"""
    <div style='font-family:Cinzel,serif; font-size:1.8rem; letter-spacing:0.18em; color:#C9A84C; margin-bottom:0.8rem;'>
        {headline}
    </div>
    <div><b>Judgment:</b> {interpretation}</div>
    """
    if specific_verdict and "General house judgment" not in specific_verdict:
        content_html += f"<br><br><b>House judgment:</b> {specific_verdict}"
    elif specific_verdict:
        content_html += f"<br><br><b>House judgment:</b> {specific_verdict}"

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
            BASIS OF JUDGMENT
        </div>
        <div><b>Lagna:</b> {judg.get('lagna_sign', 'Unknown')} | <b>Lagna lord:</b> {lagna_lord_name} in House {lagna_lord.get('house', '?') if lagna_lord else '?'}</div>
        <div><b>Moon:</b> {'Unafflicted' if judg.get('moon_unafflicted') else 'Afflicted'} | <b>Phase:</b> {judg.get('moon_phase', 'unknown').capitalize()}</div>
        <div><b>House concerned:</b> {judg.get('query_house', '?')} ({judg.get('query_house_sign', 'Unknown')}) | <b>Significator:</b> {karyesh_name} in House {karyesh.get('house', '?') if karyesh else '?'}</div>
        <div><b>Yoga:</b> {perfection}{' + Kamboola' if judg.get('kamboola_present') else ''}</div>
    </div>
    """
    st.markdown(basis_html, unsafe_allow_html=True)

    if specific_factors:
        st.markdown("<h5 style='color: #E2E2E2; margin-top: 15px;'>Classical Factors</h5>", unsafe_allow_html=True)
        for factor in specific_factors:
            st.markdown(f"- <span style='color:rgba(232,223,200,0.85);'>{factor}</span>", unsafe_allow_html=True)
    if source_rules:
        st.markdown("<h5 style='color: #E2E2E2; margin-top: 15px;'>Book Basis</h5>", unsafe_allow_html=True)
        for source in source_rules:
            st.markdown(f"- <span style='color:rgba(232,223,200,0.72);'>{source}</span>", unsafe_allow_html=True)

    if query_time_meaning:
        st.markdown(
            f"<div style='font-family:Crimson Text,serif; font-style:italic; font-size:0.95rem; color:rgba(232,223,200,0.5); margin-top:0.8rem;'><b>Time indication:</b> {query_time_meaning}</div>",
            unsafe_allow_html=True,
        )
    if primary_timing and primary_timing.get("value") is not None and judg.get("ithasala_present"):
        st.markdown(
            f"<div style='font-family:Crimson Text,serif; font-size:1rem; color:#E8DFC8; margin-top:0.5rem;'><b>Time:</b> {primary_timing.get('value')} {primary_timing.get('unit')}</div>",
            unsafe_allow_html=True,
        )

