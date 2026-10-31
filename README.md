# Multimodal Attendance & Engagement Agent

A privacy-conscious classroom analytics project combining **computer vision**, **audio signal processing**, multimodal fusion and transparent rule-based teaching suggestions. This repository includes the original Python pipeline plus a modern Streamlit web interface.

> **Decision-support only.** Engagement is a behavioural proxy, not a measure of learning or comprehension. The system does not identify students or transcribe speech. Obtain appropriate consent before recording or analysing classroom media.

## Try the web app

The Streamlit interface is `app.py`. It provides:

- **Simulated session:** a reproducible sample classroom session; no camera, microphone or media upload required.
- **Video analysis:** upload MP4, MOV, AVI or MKV for anonymous face tracking and attendance estimates.
- **Optional audio:** upload a separate 16-bit PCM WAV file for audio activity analysis. If omitted, the pipeline attempts to extract audio with ffmpeg and falls back to vision-only analysis when extraction is unavailable.
- Attendance register, engagement trend charts, signal breakdown, teaching suggestions with reasoning traces, CSV export and downloadable HTML report.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

### Run the original CLI

```bash
python main.py demo
python main.py analyze --video class.mp4 --out outputs
python main.py analyze --video class.mp4 --audio class.wav --out outputs
```

The CLI and Streamlit UI call the same pipeline modules in `src/attendance_agent/`; the original vision, audio, analytics and teaching-agent implementation is retained.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub (make it public if you want a public review link).
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
3. Select **Create app**, choose this repository and the `main` branch.
4. Set **Main file path** to `app.py`, then deploy.
5. Open the generated `*.streamlit.app` URL in a private/incognito window to verify the public demo.

No secrets or API keys are required by this project. `opencv-python-headless` is used for server deployment (no desktop GUI dependencies). The optional automatic video-audio extraction requires `ffmpeg`; for Streamlit Cloud, upload a separate compatible WAV file if ffmpeg is not available in the runtime.

## Project structure

```text
attendance_agent/
├── app.py                         # Streamlit web interface
├── main.py                        # Original CLI entry point
├── requirements.txt
├── .streamlit/config.toml
├── src/attendance_agent/
│   ├── vision.py                  # OpenCV face detection + anonymous tracking
│   ├── audio.py                   # RMS energy + adaptive voice activity detection
│   ├── analytics.py               # Attendance, fusion, trends and exports
│   ├── agent.py                   # Transparent rule-based teaching suggestions
│   ├── pipeline.py                # End-to-end demo and video analysis
│   └── ...
├── tests/
├── docs/
└── sample_output/
```

## Method summary

- **Vision:** OpenCV Haar cascades detect frontal/profile faces. A centroid tracker assigns temporary anonymous track IDs. Sustained presence is used for attendance rather than a single-frame detection.
- **Audio:** pure-NumPy frame RMS, adaptive voice-activity detection and speech-onset counting. Raw audio is not persisted by the analysis modules.
- **Fusion:** weighted visual attention, movement and audio interaction features are combined per time window. If audio is unavailable, the score is re-normalised over visual signals.
- **Teaching agent:** rule-based observations can flag attention drops, extended speech, quiet/inactive periods and engagement peaks. Each suggestion includes a reasoning trace.

## Important limitations

- Haar cascade detection is less reliable in poor lighting, occlusion and steep face angles.
- A frontal face is not proof of attention; movement and speech are not proof of engagement or learning.
- Anonymous tracker IDs are estimates and may change after occlusion or people crossing paths.
- Hosted video processing is CPU/memory constrained. Start with a short video. A cloud app cannot access the host's local webcam via camera index `0`.
- Follow applicable privacy, data-protection and institutional policies. Use only recordings for which you have permission.
