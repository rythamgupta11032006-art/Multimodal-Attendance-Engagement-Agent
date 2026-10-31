"""Streamlit interface for the Multimodal Attendance & Engagement Agent.

The original attendance_agent package remains the source of truth. This file
only provides a browser UI around its demo() and analyse() pipeline functions.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from attendance_agent import pipeline  # noqa: E402
from attendance_agent.agent import DISCLAIMER  # noqa: E402

st.set_page_config(
    page_title="ClassPulse | Attendance & Engagement",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------ visual system ------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#17243b; --muted:#718096; --blue:#356df3; --line:#e8edf5; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(180deg,#f7f9fd 0%,#f5f7fb 100%); color:var(--ink); }
.block-container { max-width:1450px; padding-top:1.7rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#111d33; }
[data-testid="stSidebar"] * { color:#edf3ff !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#b9c7df !important; }
.hero { padding:26px 30px; border-radius:22px; color:white; background:linear-gradient(115deg,#172b50 0%,#2457bb 58%,#477cf6 100%); box-shadow:0 14px 36px #244b8c24; margin-bottom:22px; }
.hero h1 { font-family:Manrope,sans-serif; font-size:30px; letter-spacing:-.8px; margin:0 0 7px 0; color:white; }
.hero p { color:#dbe7ff; margin:0; font-size:14px; }
.eyebrow { text-transform:uppercase; letter-spacing:1.5px; font-size:10px; font-weight:700; color:#bcd0ff; margin-bottom:8px; }
.section-title { font-family:Manrope,sans-serif; font-weight:800; font-size:19px; color:#17243b; margin:12px 0 3px; }
.section-sub { color:#7a879b; font-size:12px; margin-bottom:13px; }
.kpi { background:white; border:1px solid var(--line); border-radius:16px; padding:17px 18px; min-height:112px; box-shadow:0 5px 18px #1c37600a; }
.kpi-label { color:#7a879b; font-size:12px; font-weight:600; }
.kpi-value { font-family:Manrope,sans-serif; font-size:29px; font-weight:800; color:#17243b; margin-top:7px; }
.kpi-note { color:#8b97a9; font-size:11px; margin-top:1px; }
.panel { background:white; border:1px solid var(--line); border-radius:17px; padding:19px 20px; box-shadow:0 5px 18px #1c376008; }
.pill { display:inline-block; background:#eaf1ff; color:#285dd5; border-radius:30px; padding:5px 10px; font-size:11px; font-weight:700; }
div.stButton > button { border-radius:10px; font-weight:700; min-height:43px; }
.stDownloadButton > button { border-radius:10px; font-weight:700; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:14px 16px; border-radius:14px; }
hr { border-color:#e8edf5; }
.small-muted { font-size:11px; color:#8491a4; }
</style>
""", unsafe_allow_html=True)

if "result" not in st.session_state:
    st.session_state.result = None
if "run_mode" not in st.session_state:
    st.session_state.run_mode = None


def fmt_time(seconds: float) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def result_to_frames(result):
    attendance = pd.DataFrame(result.get("attendance", []))
    windows = pd.DataFrame([w.to_dict() for w in result.get("windows", [])])
    suggestions = pd.DataFrame([s.to_dict() for s in result.get("suggestions", [])])
    return attendance, windows, suggestions


def show_dashboard(result, mode):
    summary = result.get("summary", {})
    attendance, windows, suggestions = result_to_frames(result)
    detected = int(summary.get("participants_detected", 0))
    present = int(summary.get("participants_present", 0))
    engagement = float(summary.get("mean_engagement", 0) or 0)
    rate = (present / detected * 100) if detected else 0

    st.markdown('<div class="section-title">Session overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A quick read of attendance and classroom activity for this session.</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("PRESENT", f"{present}/{detected}", f"{rate:.0f}% confirmed attendance"),
        ("MEAN ENGAGEMENT", f"{engagement:.0%}", "Multimodal engagement score"),
        ("TIME WINDOWS", str(len(windows)), "30-second analysis windows"),
        ("TEACHING INSIGHTS", str(len(suggestions)), "Rule-based recommendations"),
    ]
    for col, (label, value, note) in zip((c1,c2,c3,c4), cards):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<div class="section-title">Engagement over time</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Fused attention, activity and audio interaction signals.</div>', unsafe_allow_html=True)
        if not windows.empty:
            chart_df = windows.copy()
            chart_df["time"] = chart_df["start"].apply(fmt_time)
            chart_df["engagement_pct"] = chart_df["engagement"] * 100
            fig = px.area(chart_df, x="time", y="engagement_pct", markers=True,
                          range_y=[0, 100], labels={"time":"Session time", "engagement_pct":"Engagement (%)"})
            fig.update_traces(line_color="#356df3", fillcolor="rgba(53,109,243,.12)", marker=dict(size=6))
            fig.update_layout(height=310, margin=dict(l=5,r=10,t=15,b=5),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
                              font=dict(family="DM Sans", color="#64748b"),
                              xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#edf1f7", ticksuffix="%"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No engagement windows were produced.")
    with right:
        st.markdown('<div class="section-title">Signal breakdown</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Average scores across the session.</div>', unsafe_allow_html=True)
        if not windows.empty:
            metrics = {"Attention": windows["attention"].mean(), "Activity": windows["activity"].mean()}
            if "interaction" in windows and windows["interaction"].notna().any():
                metrics["Audio interaction"] = windows["interaction"].mean()
            signal_df = pd.DataFrame({"Signal": list(metrics), "Score": [float(v)*100 for v in metrics.values()]})
            fig2 = px.bar(signal_df, x="Score", y="Signal", orientation="h", text=signal_df["Score"].map(lambda x:f"{x:.0f}%"), range_x=[0,100])
            fig2.update_traces(marker_color="#4f83f5", textposition="outside", cliponaxis=False)
            fig2.update_layout(height=245, margin=dict(l=5,r=35,t=15,b=5),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
                               font=dict(family="DM Sans", color="#64748b"),
                               xaxis=dict(showgrid=True, gridcolor="#edf1f7", ticksuffix="%"), yaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Signal metrics will appear after analysis.")

    st.markdown('<div class="section-title">Attendance register</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Anonymous participant IDs only. No face images or identity data are saved.</div>', unsafe_allow_html=True)
    if attendance.empty:
        st.info("No participants were detected in this session.")
    else:
        view = attendance.copy()
        view["first_seen_s"] = view["first_seen_s"].apply(fmt_time)
        view["last_seen_s"] = view["last_seen_s"].apply(fmt_time)
        view["presence_ratio"] = view["presence_ratio"].map(lambda x:f"{x:.0%}")
        view = view.rename(columns={"participant":"Participant", "first_seen_s":"First seen", "last_seen_s":"Last seen", "seen_seconds":"Seen (sec)", "presence_ratio":"Presence ratio", "status":"Status"})
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download attendance CSV", attendance.to_csv(index=False).encode("utf-8"), "attendance_log.csv", "text/csv")

    st.markdown('<div class="section-title">AI teaching suggestions</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Transparent, rule-based suggestions with observations and confidence scores.</div>', unsafe_allow_html=True)
    if suggestions.empty:
        st.success("No teaching suggestions were triggered for this session.")
    else:
        for _, item in suggestions.iterrows():
            with st.container(border=True):
                a, b = st.columns([4,1])
                a.markdown(f"**{str(item['category']).title()} · {fmt_time(item['start'])}–{fmt_time(item['end'])}**")
                b.markdown(f"<span class='pill'>{float(item['confidence']):.0%} confidence</span>", unsafe_allow_html=True)
                st.write(str(item["observation"]))
                st.markdown(f"**Suggested action:** {item['suggestion']}")
                with st.expander("View reasoning trace"):
                    for reason in item.get("reasoning", []):
                        st.write(f"• {reason}")

    st.markdown('<div class="section-title">Export session report</div>', unsafe_allow_html=True)
    report_path = Path(st.session_state.get("output_dir", "")) / "report.html"
    if report_path.exists():
        st.download_button("Download full HTML report", report_path.read_bytes(), "attendance_engagement_report.html", "text/html")
    st.caption(DISCLAIMER)


# --------------------------------- sidebar ----------------------------------
with st.sidebar:
    st.markdown("## 🎓 ClassPulse")
    st.markdown("**Multimodal Attendance & Engagement**")
    st.markdown("<span class='pill'>OFFLINE-FIRST ANALYTICS</span>", unsafe_allow_html=True)
    st.divider()
    page = st.radio("WORKSPACE", ["Overview", "Run a session", "About the project"], label_visibility="visible")
    st.divider()
    st.markdown("**Privacy by design**")
    st.caption("The pipeline uses anonymous track IDs and numeric audio features. It does not identify students or transcribe speech.")
    st.caption("For classroom use, obtain appropriate consent and follow your institution's recording policy.")

# ----------------------------------- pages ----------------------------------
st.markdown('''<div class="hero"><div class="eyebrow">CLASSROOM INTELLIGENCE · PROJECT DEMO</div>
<h1>Multimodal Attendance & Engagement Agent</h1>
<p>Understand attendance and classroom dynamics with privacy-conscious computer vision, audio signals and transparent AI-assisted insights.</p></div>''', unsafe_allow_html=True)

if page == "Overview":
    if st.session_state.result:
        mode_label = "SIMULATED SESSION" if st.session_state.run_mode == "demo" else "VIDEO ANALYSIS"
        st.markdown(f"<span class='pill'>{mode_label}</span>", unsafe_allow_html=True)
        show_dashboard(st.session_state.result, st.session_state.run_mode)
    else:
        st.markdown('<div class="section-title">Welcome to your classroom intelligence workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Run a no-camera demo or upload a classroom recording to generate an attendance register, engagement trends and teaching recommendations.</div>', unsafe_allow_html=True)
        a,b,c = st.columns(3)
        with a:
            st.markdown('<div class="panel"><h3>01 · Attendance</h3><p class="small-muted">Anonymous participant tracking based on sustained presence, not a single-frame detection.</p></div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="panel"><h3>02 · Engagement</h3><p class="small-muted">Combine visual attention, movement and audio activity into time-window trends.</p></div>', unsafe_allow_html=True)
        with c:
            st.markdown('<div class="panel"><h3>03 · Teaching insights</h3><p class="small-muted">Surface possible attention drops, long monologues, quiet periods and positive peaks.</p></div>', unsafe_allow_html=True)
        st.info("Start with the simulated session to explore the dashboard without a camera or classroom recording.")
        if st.button("Run sample demo session", type="primary", use_container_width=True):
            with st.spinner("Running the original attendance and engagement pipeline..."):
                out = tempfile.mkdtemp(prefix="classpulse_demo_")
                res = pipeline.demo(out)
                st.session_state.result, st.session_state.run_mode = res, "demo"
                st.session_state.output_dir = out
            st.rerun()

elif page == "Run a session":
    st.markdown('<div class="section-title">Choose your analysis mode</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Both modes use your existing Python pipeline. The simulated mode requires no media; video mode analyses an uploaded recording.</div>', unsafe_allow_html=True)
    mode = st.radio("Session type", ["Simulated classroom session", "Analyse an uploaded video"], horizontal=True)
    if mode == "Simulated classroom session":
        st.markdown('<div class="panel"><b>Safe demo mode</b><p class="small-muted">Generates a reproducible 10-minute sample session with six anonymous participants, audio activity, engagement trends and teaching suggestions. No camera or microphone is accessed.</p></div>', unsafe_allow_html=True)
        if st.button("▶ Run simulated session", type="primary", use_container_width=True):
            progress = st.progress(10, text="Preparing simulated classroom data...")
            out = tempfile.mkdtemp(prefix="classpulse_demo_")
            try:
                res = pipeline.demo(out)
                progress.progress(100, text="Analysis complete")
                st.session_state.result, st.session_state.run_mode = res, "demo"
                st.session_state.output_dir = out
                st.success("Demo session completed successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Demo failed: {exc}")
    else:
        st.markdown('<div class="panel"><b>Video analysis</b><p class="small-muted">Upload a classroom recording. The app samples frames for anonymous face tracking. You may also provide a separate 16-bit PCM WAV file for audio analysis. Without a WAV file, the pipeline attempts audio extraction using ffmpeg and falls back to vision-only if unavailable.</p></div>', unsafe_allow_html=True)
        video = st.file_uploader("Upload classroom video", type=["mp4", "mov", "avi", "mkv"], help="Use a short recording for the first test. The hosted app has limited CPU and memory.")
        wav = st.file_uploader("Optional separate audio (16-bit PCM WAV)", type=["wav"], help="Only required if you want to provide audio separately.")
        st.warning("Use recordings only with appropriate consent. The current vision model detects faces but does not identify people. It is not a validated measure of attention or learning.")
        if st.button("Analyse uploaded recording", type="primary", disabled=video is None, use_container_width=True):
            out = tempfile.mkdtemp(prefix="classpulse_video_")
            progress = st.progress(0, text="Preparing uploaded media...")
            try:
                suffix = Path(video.name).suffix or ".mp4"
                video_path = Path(out) / ("class_recording" + suffix)
                video_path.write_bytes(video.getvalue())
                audio_path = None
                if wav is not None:
                    audio_path = str(Path(out) / "class_audio.wav")
                    Path(audio_path).write_bytes(wav.getvalue())
                def update_progress(value):
                    progress.progress(min(max(int(value * 100), 0), 100), text=f"Analysing video frames... {value:.0%}")
                res = pipeline.analyse(str(video_path), out, audio_path=audio_path, progress=update_progress)
                st.session_state.result, st.session_state.run_mode = res, "video"
                st.session_state.output_dir = out
                progress.progress(100, text="Analysis complete")
                st.success("Video analysis completed. Open Overview to inspect the results.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not analyse this recording: {exc}")
                st.caption("Check that the video is valid and try a shorter MP4. If audio extraction is needed, install ffmpeg or upload a compatible WAV file.")

elif page == "About the project":
    st.markdown('<div class="section-title">How the system works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A modular, offline-first pipeline. The web app is an interface layer; the original analytics and reasoning modules remain unchanged.</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel">
    <b>Video → VisionAnalyzer → Anonymous tracks</b><br><span class="small-muted">OpenCV Haar face detection, centroid tracking, facing direction and movement proxy.</span><hr>
    <b>WAV → Audio analysis → Numeric audio windows</b><br><span class="small-muted">Frame RMS energy, adaptive voice activity detection and speech-onset counting. No speech transcription.</span><hr>
    <b>Vision + Audio → Fusion → TeachingAgent</b><br><span class="small-muted">Weighted engagement score, trend analysis and transparent rule-based teaching suggestions.</span><hr>
    <b>Analytics → CSV / JSON / HTML report</b><br><span class="small-muted">Downloadable attendance register, engagement data, suggestions and report.</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("**Important limitations**")
    st.write("- Face detection can miss people in poor lighting, at steep angles or when faces are occluded.")
    st.write("- A frontal face is only a rough attention proxy; engagement scores are not proof of attention, comprehension or learning.")
    st.write("- Anonymous tracker IDs are session-level estimates and can change after occlusion or crossing paths.")
    st.write("- Hosted video processing can be slow and is subject to platform memory, CPU and upload limits. Webcam index `0` is not available from a cloud-hosted app.")
    st.write("- Obtain consent and follow applicable privacy and institutional policies before recording or analysing classroom media.")

st.markdown("<div style='text-align:center;color:#94a0b2;font-size:11px;padding-top:28px'>CLASSPULSE · MULTIMODAL ATTENDANCE & ENGAGEMENT AGENT · ACADEMIC PROJECT DEMO</div>", unsafe_allow_html=True)
