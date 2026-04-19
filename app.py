import os

import streamlit as st

from src.query_engine import run_prasna_query, run_prasna_query_from_coords
from src.question_parser import parse_question
from src.ui import (
    configure_page,
    init_session_state,
    render_answer_block,
    render_header,
    render_input_form,
    render_parsed_question_box,
    render_sincerity_gate,
)


BSP_PATH = "de421.bsp"
BSP_URL = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp"


def ensure_ephemeris() -> None:
    if os.path.exists(BSP_PATH):
        return

    with st.spinner("Downloading ephemeris data (one time only)..."):
        try:
            import requests

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            response = requests.get(BSP_URL, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            with open(BSP_PATH, "wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    handle.write(chunk)
        except Exception as exc:
            st.error(f"Failed to download ephemeris data: {exc}")
            st.info(
                "Manual setup: Download de421.bsp from "
                "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp "
                "and place it in the project root."
            )
            st.stop()


def run_query(form_data: dict) -> None:
    st.session_state.pop("parsed_question", None)

    user_question = form_data["user_question"].strip()
    if not user_question:
        st.error("Enter one clear question before casting the chart.")
        st.session_state.last_result = None
        return

    with st.spinner("Reading your question..."):
        parsed = parse_question(user_question)
        if parsed.get("needs_clarification"):
            st.session_state["parsed_question"] = parsed
            st.session_state.last_result = None
            st.error(
                "This question is too general for Prasna Tantra. Ask one clear matter such as "
                "'Will I get the job?', 'Will I marry?', or 'Will I recover from illness?'"
            )
            return
        final_topic = parsed["query_topic"]
        final_house = parsed["query_house"]
        st.session_state["parsed_question"] = parsed

    date_str = form_data["date_query"].strftime("%Y-%m-%d")
    time_str = form_data["time_query"]

    try:
        if form_data["manual_coords"]:
            result = run_prasna_query_from_coords(
                form_data["lat_input"],
                form_data["lon_input"],
                date_str,
                time_str,
                final_topic,
                query_house_override=final_house,
            )
        else:
            result = run_prasna_query(
                form_data["city_input"],
                date_str,
                time_str,
                final_topic,
                query_house_override=final_house,
            )

        if result.get("error"):
            st.error(f"Heavens are clouded: {result['error']}")
            st.session_state.last_result = None
        else:
            st.session_state.last_result = result
    except Exception as exc:
        st.error(f"Divine connection error: {exc}")
        st.session_state.last_result = None


def main() -> None:
    configure_page()
    init_session_state()
    ensure_ephemeris()
    render_header()

    form_data = render_input_form()
    if form_data["submitted"]:
        run_query(form_data)

    if st.session_state.last_result:
        result = st.session_state.last_result
        render_sincerity_gate(result.get("sincerity", {}))
        if "parsed_question" in st.session_state:
            render_parsed_question_box(st.session_state["parsed_question"])
        render_answer_block(result)


if __name__ == "__main__":
    main()
