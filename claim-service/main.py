from fastapi import FastAPI

app = FastAPI(
    title="Microservice Gestion des Sinistres Auto",
    description="Service REST pour gérer les déclarations de sinistres automobiles",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "UP", "service": "claim-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)

