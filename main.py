"""CLI entry point.

  python main.py demo                         # synthetic session, no camera needed
  python main.py analyze --video class.mp4    # real recording (audio auto-extracted)
  python main.py analyze --video 0            # webcam index (vision only unless --audio)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from attendance_agent import pipeline  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Multimodal Attendance & Engagement Agent (offline)")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyse a recorded session")
    a.add_argument("--video", required=True)
    a.add_argument("--audio", help="optional 16-bit WAV (otherwise extracted via ffmpeg)")
    a.add_argument("--out", default="outputs")
    d = sub.add_parser("demo", help="run on a simulated session")
    d.add_argument("--out", default="outputs")
    args = p.parse_args()

    res = (pipeline.demo(args.out) if args.cmd == "demo"
           else pipeline.analyse(args.video, args.out, args.audio,
                                 progress=lambda r: print(f"\r{r:5.0%}", end="", flush=True)))
    s = res["summary"]
    print(f"\nPresent: {s.get('participants_present')}/{s.get('participants_detected')}  "
          f"mean engagement: {s.get('mean_engagement')}")
    for sg in res["suggestions"]:
        print(f" - [{sg.category}] {sg.observation} -> {sg.suggestion}")
    print(f"Report: {os.path.join(args.out, 'report.html')}")


if __name__ == "__main__":
    main()
