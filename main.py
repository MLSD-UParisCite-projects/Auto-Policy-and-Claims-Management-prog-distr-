from fastapi import FastAPI
from controllers.policy_controller import router as policy_router

app = FastAPI(
    title="Microservice Gestion des Polices d'Assurance Auto",
    description="Service REST pour gérer les contrats d'assurance automobile (Phase 1)",
    version="1.0.0",
)

app.include_router(policy_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "UP", "service": "policy-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

