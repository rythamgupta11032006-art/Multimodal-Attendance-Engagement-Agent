# Deployment checklist

## Before pushing
- [ ] Create and activate a virtual environment.
- [ ] Install `requirements.txt`.
- [ ] Run `streamlit run app.py` and test the simulated session.
- [ ] Test a short MP4 upload; test WAV upload separately if audio analysis is required.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Confirm no classroom recordings, WAV files, secrets or generated personal data are committed.

## GitHub
- [ ] Create a public repository.
- [ ] Push the complete project folder, including `app.py`, `src/`, `requirements.txt` and `.streamlit/config.toml`.
- [ ] Confirm `app.py` is in the repository root.

## Streamlit Community Cloud
- [ ] Create an app from the GitHub repository.
- [ ] Select branch `main`.
- [ ] Set main file path to `app.py`.
- [ ] Deploy and wait for the build to finish.
- [ ] Open the public URL in a private/incognito window.
- [ ] Test the simulated session and a short permitted test video.
- [ ] Submit the public Streamlit URL as the Demo Link and GitHub repository URL as the GitHub Link.
