import json
import os

import joblib
from fastapi import FastAPI, HTTPException
from google.cloud import storage
from google.oauth2 import service_account
from pydantic import BaseModel

app = FastAPI()

ARTIFACT_BUCKET = os.environ.get("ARTIFACT_BUCKET", "")
MODEL_KEY = "artifacts/current/model.joblib"
MODEL_PATH = os.path.expanduser("~/models/model.joblib")


def download_model():
    """Tải model.joblib từ cloud storage về máy khi server khởi động."""
    if not ARTIFACT_BUCKET:
        print("ARTIFACT_BUCKET not set. Skipping model download.")
        return

    creds_json = os.environ.get("GCP_CREDENTIALS_JSON")
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_info)
        client = storage.Client(credentials=creds)
    else:
        client = storage.Client()

    bucket = client.bucket(ARTIFACT_BUCKET)
    blob = bucket.blob(MODEL_KEY)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    blob.download_to_filename(MODEL_PATH)
    print("Downloaded model.joblib successfully")


download_model()
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    """GitHub Actions gọi endpoint này sau khi triển khai để xác nhận server sống."""
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    """
    Đầu vào: JSON {"features": [f1, f2, ..., f10]}
    Đầu ra:  JSON {"prediction": <0|1>, "label": <"thu_nhap_thap"|"thu_nhap_cao">}
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    if len(req.features) != 10:
        raise HTTPException(status_code=400, detail="Features must be a list of 10 floats")

    pred = model.predict([req.features])[0]

    label = "thu_nhap_cao" if pred == 1 else "thu_nhap_thap"
    return {"prediction": int(pred), "label": label}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
