"""Batch-design ElevenLabs voices for PhonyBusiness personas.

Phase 1 (design): generate previews for every persona and save them as mp3s
so you can listen before committing.
    uv run python scripts/voices/design_voices.py design

Phase 2 (create): turn the chosen preview for each persona into a permanent
voice and write voices.json (persona key -> voice_id).
    uv run python scripts/voices/design_voices.py create

To pick a preview other than the first, edit "chosen" in previews.json
(0, 1, or 2) before running phase 2.

Requires ELEVENLABS_API_KEY with Voice Generation: Access and Voices: Write.
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx

API = "https://api.elevenlabs.io/v1"
KEY = os.environ["ELEVENLABS_API_KEY"]
HEADERS = {"xi-api-key": KEY, "Content-Type": "application/json"}

HERE = Path(__file__).resolve().parent
PERSONAS_FILE = HERE / "personas.json"
PREVIEWS_FILE = HERE / "previews.json"
VOICES_FILE = HERE / "voices.json"
PREVIEW_DIR = HERE / "voice_previews"

# Settings that make designed voices sound more human.
MODEL_ID = "eleven_ttv_v3"   # newer, more expressive design model
GUIDANCE_SCALE = 3           # lower = less robotic; default is 5
REALISM = (
    " Sounds like a real person on a phone call, not a narrator or announcer:"
    " natural conversational rhythm, small pauses, slight breaths, and relaxed,"
    " imperfect everyday speech."
)


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def design():
    personas = json.loads(PERSONAS_FILE.read_text())
    previews = load_json(PREVIEWS_FILE, {})
    PREVIEW_DIR.mkdir(exist_ok=True)

    for p in personas:
        key = p["key"]
        if key in previews:
            print(f"skip {key}: already designed (delete it from previews.json to redo)")
            continue

        body = {
            "voice_description": p["description"] + REALISM,
            "model_id": MODEL_ID,
            "guidance_scale": GUIDANCE_SCALE,
        }
        if p.get("preview_text"):
            body["text"] = p["preview_text"]
        else:
            body["auto_generate_text"] = True

        r = httpx.post(f"{API}/text-to-voice/design", headers=HEADERS, json=body, timeout=180)
        if r.status_code != 200:
            print(f"FAILED {key}: HTTP {r.status_code} {r.text[:300]}")
            continue

        ids = []
        for i, prev in enumerate(r.json().get("previews", [])):
            audio = prev.get("audio_base_64") or prev.get("audio_base64")
            if audio:
                (PREVIEW_DIR / f"{key}_{i}.mp3").write_bytes(base64.b64decode(audio))
            ids.append(prev["generated_voice_id"])

        previews[key] = {"generated_voice_ids": ids, "chosen": 0}
        PREVIEWS_FILE.write_text(json.dumps(previews, indent=2))  # save after each persona
        print(f"designed {key}: {len(ids)} previews in {PREVIEW_DIR.name}/")
        time.sleep(1)

    print("\nListen to the mp3s, set 'chosen' in previews.json, then run: uv run python scripts/voices/design_voices.py create")


def create():
    personas = {p["key"]: p for p in json.loads(PERSONAS_FILE.read_text())}
    previews = json.loads(PREVIEWS_FILE.read_text())
    voices = load_json(VOICES_FILE, {})

    for key, info in previews.items():
        if key in voices:
            print(f"skip {key}: already created ({voices[key]})")
            continue
        p = personas[key]
        chosen = info["generated_voice_ids"][info.get("chosen", 0)]
        others = [g for g in info["generated_voice_ids"] if g != chosen]

        body = {
            "voice_name": f"PhonyBusiness - {p['name']}",
            "voice_description": p["description"],
            "generated_voice_id": chosen,
            "labels": {"project": "phonybusiness", "persona": key},
            "played_not_selected_voice_ids": others,
        }
        r = httpx.post(f"{API}/text-to-voice", headers=HEADERS, json=body, timeout=60)
        if r.status_code != 200:
            print(f"FAILED {key}: HTTP {r.status_code} {r.text[:300]}")
            continue

        voices[key] = r.json()["voice_id"]
        VOICES_FILE.write_text(json.dumps(voices, indent=2))  # save after each persona
        print(f"created {key}: {voices[key]}")

    print(f"\nDone. Voice IDs are in {VOICES_FILE}")


if __name__ == "__main__":
    {"design": design, "create": create}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()