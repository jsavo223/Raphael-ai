from fastapi import FastAPI

app = FastAPI(title="Raphael AI")


@app.get("/")
def health():
    return {
        "status": "online",
        "service": "raphael-ai"
    }