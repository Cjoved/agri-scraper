"""
OpenStatv2 Streamlit UI — run one scraper and watch live CMD-style output.

From project root:
  streamlit run ui/app.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

UI_DIR = Path(__file__).resolve().parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from runner import SubprocessJob  # noqa: E402
from sources import SCRAPER_SOURCES, get_source_by_label  # noqa: E402
from utils import describe_output  # noqa: E402

st.set_page_config(
    page_title="OpenStatv2 Scraper",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

POLL_SECONDS = 0.35


def _init_state() -> None:
    defaults = {
        "job": None,
        "log_text": "",
        "last_exit_code": None,
        "last_source_label": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_outputs(source_label: str | None) -> None:
    if not source_label:
        return
    source = get_source_by_label(source_label)
    if not source:
        return

    st.subheader("Expected outputs")
    rows = []
    for out in source.outputs:
        info = describe_output(out.path, out.kind)
        rows.append(
            {
                "Output": out.label,
                "Path": info["path"],
                "Exists": info["exists"],
                "Detail": info["detail"],
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _poll_running_job() -> None:
    job: SubprocessJob | None = st.session_state.job
    if job is None or job.done:
        return
    st.session_state.log_text = job.get_log_text()
    time.sleep(POLL_SECONDS)
    st.rerun()


def main() -> None:
    _init_state()

    st.title("OpenStatv2 Scraper Console")
    st.caption("Run one source at a time — same behavior as `python main.py`, with live terminal output.")

    with st.sidebar:
        st.header("Scraper")
        labels = [s.label for s in SCRAPER_SOURCES]
        selected_label = st.selectbox(
            "Choose source to run",
            labels,
            index=0,
            disabled=st.session_state.job is not None and not st.session_state.job.done,
        )
        source = get_source_by_label(selected_label)
        if source and source.warning:
            st.warning(source.warning)
        st.info("Only one source runs per job. Flags are passed via subprocess env (your `.env` file is not edited).")

        st.divider()
        st.markdown("**Format reference**")
        st.markdown("`docs/sample_corpus_outputs.jsonc`")

    job: SubprocessJob | None = st.session_state.job
    running = job is not None and not job.done

    col_run, col_stop, col_clear = st.columns([1, 1, 2])
    with col_run:
        run_clicked = st.button("Run scraper", type="primary", disabled=running)
    with col_stop:
        stop_clicked = st.button("Stop", disabled=not running)
    with col_clear:
        clear_clicked = st.button("Clear log", disabled=running)

    if clear_clicked and not running:
        st.session_state.log_text = ""
        st.session_state.last_exit_code = None

    if stop_clicked and running and job:
        job.stop()
        st.session_state.log_text = job.get_log_text()
        st.warning("Stop requested — terminating subprocess…")
        time.sleep(0.5)
        st.rerun()

    if run_clicked and not running:
        if source is None:
            st.error("Unknown source selected.")
            return
        st.session_state.job = SubprocessJob(source.env)
        st.session_state.job.start()
        st.session_state.log_text = ""
        st.session_state.last_source_label = selected_label
        st.session_state.last_exit_code = None
        st.rerun()

    # Active or finished job
    if job is not None:
        st.session_state.log_text = job.get_log_text()
        status_label = f"Running: {st.session_state.last_source_label or 'scraper'}…"
        state = "running"
        if job.done:
            st.session_state.last_exit_code = job.returncode
            if job.stopped:
                status_label = "Stopped by user"
                state = "error"
            elif job.returncode == 0:
                status_label = "Completed successfully"
                state = "complete"
            else:
                status_label = f"Failed (exit code {job.returncode})"
                state = "error"

        with st.status(status_label, expanded=True, state=state):
            st.code(st.session_state.log_text or "(waiting for output…)", language=None)

        if not job.done:
            _poll_running_job()
            return

        # Job finished
        if job.returncode == 0 and not job.stopped:
            st.success("Scraper finished.")
        elif job.stopped:
            st.warning("Run was stopped before completion.")
        else:
            st.error(f"Scraper exited with code {job.returncode}.")

        _render_outputs(st.session_state.last_source_label)
        st.session_state.job = None
        return

    # Idle: show last log if any
    if st.session_state.log_text:
        st.subheader("Last run log")
        st.code(st.session_state.log_text, language=None)
        if st.session_state.last_exit_code is not None:
            st.caption(f"Exit code: {st.session_state.last_exit_code}")
        _render_outputs(st.session_state.last_source_label)
    else:
        st.info("Select a scraper in the sidebar, then click **Run scraper**.")


if __name__ == "__main__":
    main()
