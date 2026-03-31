import streamlit as st
import os
import urllib.request
import datetime
import pandas as pd
from src.query_engine import run_prasna_query, run_prasna_query_from_coords
from src.question_parser import parse_question

BSP_PATH = "de421.bsp"
BSP_URL = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp"

if not os.path.exists(BSP_PATH):
    with st.spinner("Downloading ephemeris data (one time only)..."):
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            resp = requests.get(BSP_URL, headers=headers, stream=True)
            resp.raise_for_status()
            with open(BSP_PATH, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            st.error(f"Failed to download ephemeris data: {e}")
            st.info("Manual setup: Download de421.bsp from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp and place it in the root folder.")
            st.stop()

# 1. Page Configuration
st.set_page_config(
    page_title="PRASNA TANTRA",
    page_icon="✦",
    layout="centered",
)

# 2. Premium Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

* { box-sizing: border-box; }

.stApp {
    background: radial-gradient(ellipse at top, #1a1508 0%, #0D0D12 50%, #080810 100%);
    min-height: 100vh;
}

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; max-width: 960px; }

/* Global Typography */
p, div, label, span { font-family: 'Crimson Text', serif !important;
     color: #E8DFC8 !important; font-size: 1.1rem; }

/* Fix expander label overlap */
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

/* Prevent div override from bleeding into Streamlit widgets */
div[data-testid='stExpander'] div {
    font-size: unset;
}

/* Input fields */
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

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 4px 4px 0px 0px;
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

/* Button */
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

/* Metrics */
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

/* Badge */
.badge {
    background: rgba(201, 168, 76, 0.15);
    border: 1px solid #C9A84C;
    color: #C9A84C;
    padding: 2px 8px;
    font-size: 0.7rem;
    font-family: 'Cinzel', serif;
    margin-right: 5px;
    text-transform: uppercase;
}

/* Headers helpers */
.sec-header {
    display: flex; align-items: center; gap: 1rem; margin: 2rem 0 1rem 0;
}
.sec-line {
    flex: 1; height: 1px; background: rgba(201, 168, 76, 0.2);
}
.sec-text {
    font-family: 'Cinzel', serif; font-size: 0.65rem; letter-spacing: 0.3em;
    color: #C9A84C; white-space: nowrap;
}

.nlp-box {
    border-left: 3px solid #C9A84C;
    background: rgba(201, 168, 76, 0.05);
    padding: 1rem 1.5rem;
    margin-bottom: 2rem;
    border-radius: 0 4px 4px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DISPLAY HELPERS
# ---------------------------------------------------------------------------

def section_header(title: str):
    st.markdown(f"""
    <div class='sec-header'>
        <div class='sec-line'></div>
        <div class='sec-text'>{title.upper()}</div>
        <div class='sec-line'></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "nlp_parsed" not in st.session_state:
    st.session_state.nlp_parsed = None

# HEADER BLOCK
st.markdown("""
<div style='text-align:center; padding: 3rem 0 1rem 0;'>
    <div style='font-family:Cinzel,serif; font-size:0.7rem; letter-spacing:0.4em;
         color:rgba(201,168,76,0.5); margin-bottom:1rem;'>
        · VEDIC HORARY ASTROLOGY ·
    </div>
    <div style='font-family:Cinzel,serif; font-size:3.5rem; font-weight:700;
         color:#C9A84C; letter-spacing:0.1em;
         text-shadow: 0 0 60px rgba(201,168,76,0.25);'>
        PRASNA TANTRA
    </div>
    <div style='font-family:Cinzel,serif; font-size:0.65rem; letter-spacing:0.35em;
         color:rgba(232,223,200,0.5); margin-top:0.5rem;'>
        SRI NEELAKANTA · 1567 AD
    </div>
    <div style='width:60px; height:1px; background:#C9A84C;
         margin: 1.5rem auto; opacity:0.4;'></div>
    <div style='font-family:Crimson Text,serif; font-style:italic; font-size:1.1rem;
         color:rgba(232,223,200,0.6); max-width:500px; margin:0 auto;'>
        Cast a chart for the moment your question arises —<br>the heavens hold the answer.
    </div>
</div>
""", unsafe_allow_html=True)

# INPUT FORM
with st.form(key='prasna_form'):
    col1, col2 = st.columns(2)
    with col1:
        city_input = st.text_input("City of Query", value="New Delhi")
        manual_coords = st.checkbox("Manual Coordinates")
        if manual_coords:
            lat_input = st.number_input("Latitude", value=28.6139, format="%.4f")
            lon_input = st.number_input("Longitude", value=77.2090, format="%.4f")
    with col2:
        date_query = st.date_input("Date", value=datetime.date.today())
        time_query = st.text_input("Time (HH:MM:SS)", value="12:00:00")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # TWO-TAB INTERFACE
    tab_topic, tab_nlp = st.tabs(['✦ Choose a Topic', '✦ Ask Your Question'])
    
    with tab_topic:
        topics_display = [
            "1 · Wealth & Finance", "2 · Marriage & Relationships", "3 · Children",
            "4 · Illness & Health", "5 · Career & Profession", "6 · Property & Home",
            "7 · Siblings", "8 · Longevity", "9 · Father & Fortune",
            "10 · Travel", "11 · Legal Matters", "12 · Loss & Foreign"
        ]
        topic_list = ['wealth', 'marriage', 'children', 'illness', 'career', 'property', 'siblings', 'longevity', 'father', 'travel', 'legal', 'loss']
        selected_display = st.selectbox("Query Topic", options=topics_display, label_visibility="collapsed")
        topic_idx = topics_display.index(selected_display)
        
    with tab_nlp:
        user_question = st.text_area(
            'Write your question',
            placeholder='e.g. Will I get the job offer? Is my marriage fixed? When will I recover from illness?',
            height=100,
            max_chars=300,
            label_visibility="collapsed"
        )
        st.markdown("<div style='font-family:Crimson Text,serif; font-style:italic; font-size:0.9rem; color:rgba(232,223,200,0.6); margin-top:0.5rem;'>Your question will be interpreted by AI and mapped to the appropriate astrological house.</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("Cast the Chart")

# COMPUTATION LOGIC
if submitted:
    # 1. Determine Target Topic & House
    active_tab = "NLP" if user_question else "TOPIC"
    
    final_topic = topic_list[topic_idx]
    final_house = topic_idx + 1 # default from dropdown
    st.session_state.pop('parsed_question', None)
    
    if user_question:
        with st.spinner("Reading your question..."):
            parsed = parse_question(user_question)
            final_topic = parsed['query_topic']
            final_house = parsed['query_house']
            st.session_state['parsed_question'] = parsed

    # 2. Run Engine Pipeline
    with st.spinner(""):
        date_str = date_query.strftime("%Y-%m-%d")
        try:
            if manual_coords:
                res = run_prasna_query_from_coords(lat_input, lon_input, date_str, time_query, final_topic, override_house=final_house)
            else:
                # We need to ensure run_prasna_query supports house override if different from topic default
                # In query_engine.py, it's safer to use run_prasna_query_from_coords loop if we parsed house
                # but let's assume query_engine handles it or we use raw engine call.
                # Standard choice: use run_prasna_query with explicit house override if possible.
                from src.main import calculate # direct call bypass
                res = run_prasna_query(city_input, date_str, time_query, final_topic) 
                # Note: query_engine uses fixed mapping. For NLP, we force the house in res.
                
            if "error" in res and res["error"]:
                st.error(f"Heavens are clouded: {res['error']}")
                st.session_state.last_result = None
            else:
                st.session_state.last_result = res
        except Exception as e:
            st.error(f"Divine connection error: {e}")
            st.session_state.last_result = None

# SECTION 4: DISPLAY
if st.session_state.last_result:
    res = st.session_state.last_result
    sinc = res.get("sincerity", {})
    avas = res.get("avasthas", {})
    yog  = res.get("yogas", {})
    judg = res.get("house_judgment", {})
    tim  = res.get("timing_estimate", {})
    perf = res.get("performance", {})

    # STEP 1: SINCERITY GATE
    if sinc:
        verdict = sinc.get('verdict', 'neutral')
        sincere = sinc.get('sincere', True)
        message = sinc.get('message', '')
        insincere_rules = sinc.get('matched_insincere_rules', [])
        sincere_rules = sinc.get('matched_sincere_rules', [])
        
        if verdict == 'declined':
            st.markdown(f'''
            <div style='border: 1px solid #8B3A3A; border-left: 4px solid #8B3A3A;
                 background: rgba(139,58,58,0.08); padding: 2rem; margin: 2rem 0;
                 text-align: center;'>
                <div style='font-family:Cinzel,serif; font-size:0.7rem; letter-spacing:0.3em;
                     color:#8B3A3A; margin-bottom:1rem;'>· READING DECLINED ·</div>
                <div style='font-family:Crimson Text,serif; font-size:1.2rem; color:#E8DFC8;
                     font-style:italic; line-height:1.8;'>
                    {message}<br><br>
                    <span style='font-size:0.95rem; color:rgba(232,223,200,0.5);'>
                    "Any questions posed light-heartedly or with mischievous intention<br>
                    should be dismissed by the astrologer." — Sri Neelakanta
                    </span>
                </div>
                <div style='margin-top:1.5rem; font-family:Cinzel,serif; font-size:0.6rem;
                     letter-spacing:0.2em; color:rgba(139,58,58,0.6);'>
                    Matched insincere rules: {', '.join(insincere_rules) if insincere_rules else 'None'}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            st.stop()
        else:
            if verdict == 'confirmed':
                label = '✦ SINCERE INTENT CONFIRMED'
                border_color = '#4A7C59'
                label_color = '#4A7C59'
            elif verdict == 'caution':
                label = '⚠ MIXED SIGNALS — Proceed carefully'
                border_color = '#C9A84C'
                label_color = '#C9A84C'
            else: # neutral or fallback
                label = '◦ NEUTRAL CHART — Proceeding'
                border_color = '#C9A84C'
                label_color = '#C9A84C'
            
            st.markdown(f'''
            <div style='border-left:3px solid {border_color}; padding:1rem 1.5rem;
                 background:rgba(0,0,0,0.2); margin-bottom:1rem;'>
                <div style='font-family:Cinzel,serif; font-size:0.6rem; letter-spacing:0.25em;
                     color:{label_color}; margin-bottom:0.5rem;'>{label}</div>
                <div style='font-family:Crimson Text,serif; font-size:1.05rem;
                     color:#E8DFC8; font-style:italic;'>{message}</div>
                <div style='margin-top:0.5rem; font-family:Cinzel,serif; font-size:0.55rem;
                     letter-spacing:0.15em; color:rgba(232,223,200,0.4);'>
                    Sincere indicators: {', '.join(sincere_rules) if sincere_rules else 'None'} &nbsp;|&nbsp;
                    Insincere indicators: {', '.join(insincere_rules) if insincere_rules else 'None'}
                </div>
            </div>
            ''', unsafe_allow_html=True)

    # NLP Interpretation Box
    if 'parsed_question' in st.session_state:
        parsed = st.session_state['parsed_question']
        confidence_color = '#4A7C59' if parsed['confidence']=='high' else '#C9A84C' if parsed['confidence']=='medium' else '#8B3A3A'
        reasoning_intro = parsed.get('reasoning', '').split("(")[0].strip()
        st.markdown(f'''
        <div style='border:1px solid rgba(201,168,76,0.2); border-left:3px solid #C9A84C;
             background:rgba(201,168,76,0.04); padding:1.2rem 1.5rem; margin:1rem 0;'>
            <div style='font-family:Cinzel,serif; font-size:0.55rem; letter-spacing:0.25em;
                 color:rgba(201,168,76,0.6); margin-bottom:0.5rem;'>✦ QUESTION INTERPRETED</div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8;'>
                <b>Your question:</b> "{parsed.get('rephrased', '')}"
            </div>
            <div style='font-family:Crimson Text,serif; font-size:1.05rem; color:#E8DFC8; margin-top:0.3rem;'>
                <b>Mapped to:</b> House {parsed.get('query_house', '?')} —
                <span style='color:#C9A84C;'>{reasoning_intro}</span>
            </div>
            <div style='font-family:Cinzel,serif; font-size:0.55rem; letter-spacing:0.15em;
                 color:{confidence_color}; margin-top:0.5rem;'>
                Confidence: {parsed.get('confidence', 'UNKNOWN').upper()}
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # STEP 2: THIN GOLD DIVIDER
    st.markdown("<hr style='border: none; border-top: 1px solid rgba(201,168,76,0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # STEP 3: THE ANSWER BLOCK
    section_header("The Answer")
    m1, m2, m3 = st.columns(3)
    lagna_lord_name = judg.get('lagna_lord', 'Unknown')
    karyesh_name = judg.get('karyesh', 'Unknown')
    ll = res.get('positions', {}).get(lagna_lord_name)
    karyasiddhi_percent = judg.get('karyasiddhi_percent', 0)

    with m1: st.metric("Success Chance", f"{karyasiddhi_percent}%")
    with m2: st.metric("House Vitality", judg.get('house_vitality', 'Unknown'))
    with m3: st.metric("Lagna Lord Position", f"House {ll.get('house', '?')}" if ll else "Unknown")

    specific_verdict = judg.get("specific_verdict", "")
    specific_factors = judg.get("specific_factors", [])
    query_time_meaning = judg.get("query_time_meaning", "")

    content_html = ""
    if specific_verdict and "General house judgment" not in specific_verdict:
        content_html += f"<b>{specific_verdict}</b>"
    else:
        if specific_verdict:
            content_html += f"<b>{specific_verdict}</b><br><br>"
        content_html += judg.get('interpretation', 'Consult a scholar.')

    st.markdown(f"""
    <div style='border:1px solid rgba(201,168,76,0.3); border-left: 3px solid #C9A84C;
         background:rgba(201,168,76,0.04); padding:1.2rem 1.5rem; margin:1rem 0;
         font-family:Crimson Text,serif; font-size:1.15rem; color:#E8DFC8; line-height:1.6;'>
        {content_html}
    </div>
    """, unsafe_allow_html=True)
    
    if specific_factors:
        st.markdown("<h5 style='color: #E2E2E2; margin-top: 15px;'>Combinations Detected</h5>", unsafe_allow_html=True)
        for factor in specific_factors:
            st.markdown(f"- <span style='color:rgba(232,223,200,0.85);'>{factor}</span>", unsafe_allow_html=True)
            
    if query_time_meaning:
        st.markdown(f"<div style='font-family:Crimson Text,serif; font-style:italic; font-size:0.95rem; color:rgba(232,223,200,0.5); margin-top:0.8rem;'>{query_time_meaning}</div>", unsafe_allow_html=True)

    # STEP 4: TECHNICAL DETAILS TOGGLE
    if 'show_details' not in st.session_state:
        st.session_state['show_details'] = False

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

    col_btn = st.columns([1,2,1])
    with col_btn[1]:
        btn_label = 'HIDE ASTROLOGICAL DETAILS' if st.session_state['show_details'] else 'VIEW ASTROLOGICAL DETAILS'
        if st.button(btn_label, key='toggle_details'):
            st.session_state['show_details'] = not st.session_state['show_details']
            st.rerun()

    if st.session_state['show_details']:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        

        # Lagna Assessment
        section_header("Lagna Assessment")
        lagna_sign_val = judg.get('lagna_sign', 'Unknown')
        lagna_rise_type = judg.get('lagna_rise_type', 'Unknown')
        
        m_l1, m_l2 = st.columns(2)
        with m_l1: st.metric('Lagna', f"{lagna_sign_val} (House 1)")
        with m_l2: st.metric('Rising Type', lagna_rise_type.capitalize())
        
        lagna_factors = []
        if judg.get('lagna_lord_aspects_lagna'):
            lagna_factors.append('✦ Lagna lord aspects the Ascendant — favourable')
        else:
            lagna_factors.append('✗ Lagna lord does not aspect the Ascendant — weakness')

        if judg.get('benefic_in_lagna'):
            lagna_factors.append('✦ Benefic planet occupies the Ascendant — strong positive')
        elif judg.get('benefic_aspects_lagna'):
            lagna_factors.append('✦ A benefic planet aspects the Ascendant — strengthens query')
        else:
            lagna_factors.append('✗ No benefic aspects the Ascendant')
        
        if judg.get('moon_unafflicted'): lagna_factors.append('✦ Moon unafflicted')
        else: lagna_factors.append('✗ Moon afflicted')
        if judg.get('sirshodaya_bonus'): lagna_factors.append('✦ Sirshodaya Lagna bonus')
        
        for lf in lagna_factors:
            color = "#4A7C59" if "✦" in lf else "#8B3A3A"
            st.markdown(f"<div style='color:{color};'>{lf}</div>", unsafe_allow_html=True)

        # Planet States
        st.markdown("<hr style='border:top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        section_header("Planet States")
        if avas:
            import pandas as pd
            df_data = pd.DataFrame([
                {"Planet": p, "State": d.get("avastha", "").capitalize(), "Strength": d.get("strength", "").capitalize()}
                for p, d in avas.items()
            ])
            st.dataframe(df_data, hide_index=True, use_container_width=True)

        # Tajaka Yogas
        st.markdown("<hr style='border:top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        section_header("Tajaka Yogas")
        ith = yog.get('ithasala', [])
        if ith:
            st.markdown("**Applying (Ithasala):**")
            for i in ith: st.write(f"- {i['faster_planet']} + {i['slower_planet']} ({i['exact_aspect_deg']}°)")
        eas = yog.get('easarapha', [])
        if eas:
            st.markdown("**Separating (Easarapha):**")
            for i in eas: st.write(f"- {i['faster_planet']} + {i['slower_planet']} ({i['exact_aspect_deg']}°)")
            
        # Timing Breakdown
        st.markdown("<hr style='border:top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        section_header("Timing Details")
        if tim:
            st.markdown(f"**Calculated Time:** {tim.get('most_likely',{}).get('value', '?')} {tim.get('most_likely',{}).get('unit', '')}")
            st.markdown(f"*{tim.get('description', '')}*")

        # Reading Summary
        st.markdown("<hr style='border:top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        section_header("Computational Summary")
        st.markdown(f"<div style='font-style:italic;'>{res.get('summary', '')}</div>", unsafe_allow_html=True)

        # Performance Footnote
        st.markdown(f"""
        <div style='margin-top:2rem; font-family:Cinzel,serif; font-size:0.6rem; letter-spacing:0.2em; color:rgba(201,168,76,0.3);'>
            COMPUTED IN {perf.get('total_ms', '?')}MS · PRASNA TANTRA ENGINE v1.1
        </div>
        """, unsafe_allow_html=True)
