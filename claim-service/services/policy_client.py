import os
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status
from models.claim import Claim

# URL du microservice policy-service (par défaut localhost:8080 en local, et http://policy-service:8080 sur Kubernetes)
POLICY_SERVICE_URL = os.getenv("POLICY_SERVICE_URL", "http://localhost:8080")


def fetch_policy(policy_id: str) -> Optional[Dict[str, Any]]:
    """
    Appelle le microservice policy-service via HTTP GET /policies/{policy_id}.
    Retourne le dictionnaire de la police si elle existe, None si 404,
    ou lève une erreur 503 si policy-service est injoignable.
    """
    url = f"{POLICY_SERVICE_URL}/policies/{policy_id}"
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            if response.status_code == status.HTTP_404_NOT_FOUND:
                return None
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Impossible de joindre le microservice policy-service ({POLICY_SERVICE_URL}) : {exc}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Erreur retournée par policy-service : {exc.response.text}",
        )


def evaluate_claim_with_policy(claim: Claim, policy_data: Dict[str, Any]) -> None:
    """
    Évalue un sinistre par rapport aux garanties du contrat récupéré depuis policy-service :
    - Vérifie que le statut de la police est ACTIVE.
    - Calcule le montant approuvé (approved_amount) en déduisant la franchise (deductible)
      et en appliquant le plafond de garantie (coverageLimit).
    """
    policy_status = (policy_data.get("status") or "").upper()
    if policy_status != "ACTIVE":
        claim.status = "REJECTED"
        claim.approved_amount = 0.0
        claim.rejection_reason = f"La police '{claim.policy_id}' n'est pas active (statut actuel : {policy_status})."
        return

    deductible = float(policy_data.get("deductible") or 0.0)
    coverage_limit = float(policy_data.get("coverageLimit") or 0.0)

    # Calcul du remboursement après franchise
    net_amount = max(0.0, claim.claimed_amount - deductible)

    # Application du plafond de garantie s'il est défini (> 0)
    if coverage_limit > 0:
        net_amount = min(net_amount, coverage_limit)

    claim.approved_amount = round(net_amount, 2)
    if claim.status == "PENDING" and claim.approved_amount > 0:
        claim.status = "APPROVED"
        claim.rejection_reason = None

