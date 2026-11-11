from fastapi import FastAPI
from controllers.policy_controller import router as policy_router

# ==============================================================================
# NOTE D'ARCHITECTURE (RAPPEL) :
# 1. Communication Utilisateur <-> Microservice : API REST (FastAPI sur le port 8080)
# 2. Communication Inter-Microservices (claim-service <-> policy-service) :
#    -> TODO (Phase suivante quand on ) : Ajouter un serveur gRPC (ex: port 50051) avec Protobuf
#       pour que claim-service vérifie les polices auprès de policy-service via gRPC.
# ==============================================================================

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

