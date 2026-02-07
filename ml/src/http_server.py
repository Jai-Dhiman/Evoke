from typing import Optional

from fastapi import FastAPI, File, UploadFile

from src.audio_encoder import AudioEncoder
from src.bridge import CrossModalBridge

app = FastAPI()

audio_encoder: Optional[AudioEncoder] = None
bridge: Optional[CrossModalBridge] = None


@app.on_event("startup")
async def startup():
    global audio_encoder, bridge
    print("Loading models...")
    audio_encoder = AudioEncoder()
    audio_encoder.load_model()
    bridge = CrossModalBridge()
    bridge.load_model()
    print("Models loaded successfully")


@app.post("/analyze")
async def analyze(audio: UploadFile = File(...)):
    if audio_encoder is None or bridge is None:
        raise RuntimeError("Models not loaded")

    audio_data = await audio.read()
    audio_format = audio.filename.rsplit(".", 1)[-1] if audio.filename and "." in audio.filename else "wav"

    embedding, mood = audio_encoder.encode(audio_data, audio_format)
    clip_embedding = bridge.project_to_clip_space(embedding)

    return {
        "embedding": clip_embedding.tolist(),
        "mood_energy": float(mood["energy"]),
        "mood_valence": float(mood["valence"]),
        "mood_tempo": float(mood["tempo"]),
        "mood_texture": float(mood["texture"]),
    }


@app.get("/health")
async def health():
    return {"healthy": True, "message": "ML service is running"}
