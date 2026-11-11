import os
from typing import Any, Dict, Optional
import httpx
from fastapi import FastAPI, Body, HTTPException, Query, Request, Response

# ==============================================================================
# API GATEWAY - Point d'entrée unique (Single Entry Point) pour les clients REST
# - Port local / conteneur : 8000 (NodePort Kubernetes : 30000)
# - Redirige /policies/*  ---> policy-service (http://policy-service:8080)
# - Redirige /claims/*    ---> claim-service  (http://claim-service:8081)
# ==============================================================================

POLICY_SERVICE_URL = os.getenv("POLICY_SERVICE_URL", "http://localhost:8080")
CLAIM_SERVICE_URL = os.getenv("CLAIM_SERVICE_URL", "http://localhost:8081")

app = FastAPI(
    title="API Gateway - Gestion Polices & Sinistres Auto",
    description=(
        "Point d'entrée unique (API Gateway REST) qui route les requêtes des utilisateurs "
        "vers les microservices internes (policy-service et claim-service)."
    ),
    version="1.0.0",
)


async def forward_request(
    target_base_url: str,
    path: str,
    request: Request,
) -> Response:
    """Fonction générique de Reverse Proxy HTTP asynchrone vers un microservice cible."""
    url = f"{target_base_url}{path}"
    query_params = dict(request.query_params)
    body = await request.body()
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                params=query_params,
                content=body,
                headers=headers,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type", "application/json"),
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"API Gateway : Le microservice cible ({target_base_url}) est injoignable ({exc}).",
        )


@app.get("/health", tags=["Gateway Health"])
async def gateway_health():
    """Vérifie l'état de l'API Gateway et du microservice policy-service."""
    policy_status = "DOWN"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{POLICY_SERVICE_URL}/health")
            if r.status_code == 200:
                policy_status = "UP"
    except httpx.RequestError:
        policy_status = "DOWN"

    return {
        "gateway": "UP",
        "routes": {
            "policy-service": {"url": POLICY_SERVICE_URL, "status": policy_status},
            "claim-service": {"url": CLAIM_SERVICE_URL},
        },
    }


# ==============================================================================
# ROUTES EXPLICITES POUR SWAGGER UI (/docs) -> POLICY-SERVICE
# ==============================================================================

@app.get("/policies", tags=["Policies (via Gateway)"], summary="Lister toutes les polices")
async def get_policies(
    request: Request,
    status: Optional[str] = Query(None, description="Filtrer par statut (ex: ACTIVE)"),
    clientId: Optional[str] = Query(None, description="Filtrer par identifiant client"),
):
    return await forward_request(POLICY_SERVICE_URL, "/policies", request)


@app.get("/policies/{policy_id}", tags=["Policies (via Gateway)"], summary="Récupérer une police par son ID")
async def get_policy_by_id(policy_id: str, request: Request):
    return await forward_request(POLICY_SERVICE_URL, f"/policies/{policy_id}", request)


@app.post("/policies", status_code=201, tags=["Policies (via Gateway)"], summary="Créer une nouvelle police")
async def create_policy(request: Request, payload: Dict[str, Any] = Body(...)):
    return await forward_request(POLICY_SERVICE_URL, "/policies", request)


@app.put("/policies/{policy_id}", tags=["Policies (via Gateway)"], summary="Mettre à jour une police")
async def update_policy(policy_id: str, request: Request, payload: Dict[str, Any] = Body(...)):
    return await forward_request(POLICY_SERVICE_URL, f"/policies/{policy_id}", request)


@app.patch("/policies/{policy_id}/status", tags=["Policies (via Gateway)"], summary="Modifier le statut d'une police")
async def patch_policy_status(
    policy_id: str,
    request: Request,
    status: str = Query(..., description="Nouveau statut : ACTIVE, SUSPENDED, EXPIRED"),
):
    return await forward_request(POLICY_SERVICE_URL, f"/policies/{policy_id}/status", request)


@app.delete("/policies/{policy_id}", status_code=204, tags=["Policies (via Gateway)"], summary="Supprimer une police")
async def delete_policy(policy_id: str, request: Request):
    return await forward_request(POLICY_SERVICE_URL, f"/policies/{policy_id}", request)


# ==============================================================================
# PROXY GÉNÉRIQUE POUR /claims (Prêt pour le 2e microservice claim-service)
# ==============================================================================

@app.api_route(
    "/claims",
    methods=["GET", "POST"],
    tags=["Claims (via Gateway)"],
    summary="Proxy vers claim-service (/claims)",
)
async def proxy_claims_root(request: Request):
    return await forward_request(CLAIM_SERVICE_URL, "/claims", request)


@app.api_route(
    "/claims/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Claims (via Gateway)"],
    summary="Proxy vers claim-service (/claims/{path})",
)
async def proxy_claims_subpath(path: str, request: Request):
    return await forward_request(CLAIM_SERVICE_URL, f"/claims/{path}", request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

