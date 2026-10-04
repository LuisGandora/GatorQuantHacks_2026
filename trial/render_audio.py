"""Voice the Filing Trial with ElevenLabs: prosecution, defense and the Quant Judge, three distinct voices.

    python trial/build.py            # first: writes trial/data.json (the judge's lines) and checks scripts.json
    python trial/render_audio.py     # then: writes trial/audio/<accession>_<role>.mp3 and rebuilds index.html
                                     # roles: prosecution, defense, judge (verdict), judge_outcome (the reveal, judge's voice)

Needs ELEVENLABS_API_KEY in .env (gitignored) or the environment. No other key is read.
Optional overrides: ELEVENLABS_MODEL, ELEVENLABS_VOICE_PROSECUTION / _DEFENSE / _JUDGE (voice ids).
Existing MP3s are skipped, so re-running only renders what is missing; delete a file to re-record it.
ElevenLabs bills by character: the script prints the total before it calls the API.
"""
import json, os, subprocess, sys
from pathlib import Path

import requests

TRIAL = Path(__file__).resolve().parent
ROOT = TRIAL.parent
# ElevenLabs premade voices (override with the env vars above)
VOICES = {"prosecution": "pNInz6obpgDQGcFmaJgB",   # Adam
          "defense": "21m00Tcm4TlvDq8ikWAM",       # Rachel
          "judge": "VR6AewLTigWG4xSOukaG"}         # Arnold


def env_key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        k, _, v = line.partition("=")
        if k.strip() == "ELEVENLABS_API_KEY" and v.strip():
            return v.strip().strip("'\"")
    sys.exit("Set ELEVENLABS_API_KEY in .env (it is gitignored) or in the environment.")


def lines():
    scripts = json.loads((TRIAL / "scripts.json").read_text(encoding="utf-8"))
    data = json.loads((TRIAL / "data.json").read_text(encoding="utf-8"))
    if scripts.get("needs_human_review"):
        sys.exit('trial/scripts.json is still marked needs_human_review. Review the drafts, set it to false, rerun trial/build.py.')
    for d in data:
        s = scripts["filings"][d["accession_number"]]
        yield d["accession_number"], "prosecution", s["prosecution"]
        yield d["accession_number"], "defense", s["defense"]
        yield d["accession_number"], "judge", d["judge_verdict"]
        yield d["accession_number"], "judge_outcome", d["judge_outcome"]   # played only after the reveal


def main():
    todo = [(a, r, t) for a, r, t in lines() if not (TRIAL / "audio" / f"{a}_{r}.mp3").exists()]
    if not todo:
        print("all audio already rendered")
        return
    print(f"{len(todo)} clips, {sum(len(t) for _, _, t in todo):,} characters to ElevenLabs")
    key, model = env_key(), os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    (TRIAL / "audio").mkdir(exist_ok=True)
    for acc, role, text in todo:
        voice = os.environ.get(f"ELEVENLABS_VOICE_{role.split('_')[0].upper()}", VOICES[role.split("_")[0]])
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                          headers={"xi-api-key": key, "Accept": "audio/mpeg"},
                          json={"text": text, "model_id": model}, timeout=120)
        if r.status_code != 200:
            sys.exit(f"{acc} {role}: ElevenLabs returned {r.status_code}: {r.text[:300]}")
        (TRIAL / "audio" / f"{acc}_{role}.mp3").write_bytes(r.content)
        print(f"  {acc} {role}: {len(r.content) // 1024} KB")
    subprocess.run([sys.executable, str(TRIAL / "build.py"), *dict.fromkeys(a for a, _, _ in lines())], check=True)


if __name__ == "__main__":
    main()
