from datetime import date
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Body, HTTPException, Query, status
from models.claim import Claim
from services.policy_client import fetch_policy, evaluate_claim_with_policy

router = APIRouter(prefix="/claims", tags=["Claims"])

# Base de données en mémoire avec exemples utilisant @Builder et le constructeur simplifié à 4 champs
claims_db: Dict[str, Claim] = {
    "CLM-2026-001": (
        Claim.builder()
        .claim_id("CLM-2026-001")
        .policy_id("POL-2026-001")
        .description("Accrochage pare-chocs avant sur parking")
        .claimed_amount(1200.0)
        .approved_amount(900.0)  # 1200 - 300 (franchise de POL-2026-001)
        .status("APPROVED")
        .incident_date(date(2026, 3, 15))
        .declaration_date(date(2026, 3, 16))
        .build()
    ),
    # Constructeur simplifié avec uniquement les 4 champs de base (status = "PENDING" par défaut)
    "CLM-2026-002": Claim("CLM-2026-002", "POL-2026-002", "Bris de glace pare-brise avant", 350.0),
}


@router.get("", summary="Lister tous les sinistres")
def get_all_claims(
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut (PENDING, APPROVED, REJECTED)"),
    policy_id: Optional[str] = Query(None, alias="policyId", description="Filtrer par identifiant de police"),
) -> List[Dict[str, Any]]:
    results = list(claims_db.values())
    if status_filter:
        results = [c for c in results if c.status.upper() == status_filter.upper()]
    if policy_id:
        results = [c for c in results if c.policy_id == policy_id]
    return [c.to_dict() for c in results]


@router.get("/{claim_id}", summary="Récupérer un sinistre par son ID")
def get_claim_by_id(claim_id: str) -> Dict[str, Any]:
    claim = claims_db.get(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sinistre '{claim_id}' introuvable.",
        )
    return claim.to_dict()


@router.get("/{claim_id}/details", summary="Récupérer un sinistre enrichi avec les détails de sa police (appel inter-service)")
def get_claim_with_policy_details(claim_id: str) -> Dict[str, Any]:
    claim = claims_db.get(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sinistre '{claim_id}' introuvable.",
        )
    policy_data = fetch_policy(claim.policy_id) if claim.policy_id else None
    result = claim.to_dict()
    result["policy"] = policy_data
    return result


@router.post("", status_code=status.HTTP_201_CREATED, summary="Déclarer un nouveau sinistre (vérifie la police auprès de policy-service)")
def create_claim(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    claim = Claim.from_dict(payload)
    if not claim.claim_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le champ 'claimId' (ou 'claim_id') est obligatoire.",
        )
    if not claim.policy_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le champ 'policyId' (ou 'policy_id') est obligatoire.",
        )
    if claim.claim_id in claims_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un sinistre avec l'ID '{claim.claim_id}' existe déjà.",
        )

    # Appel HTTP synchrone au microservice policy-service pour vérifier l'existence et le statut du contrat
    policy_data = fetch_policy(claim.policy_id)
    if not policy_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Impossible de créer le sinistre : la police '{claim.policy_id}' n'existe pas dans policy-service.",
        )

    # Calcul automatique de l'indemnisation et du statut selon la police récupérée
    evaluate_claim_with_policy(claim, policy_data)

    claims_db[claim.claim_id] = claim
    return claim.to_dict()


@router.put("/{claim_id}", summary="Mettre à jour un sinistre existant")
def update_claim(claim_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sinistre '{claim_id}' introuvable.",
        )
    updated_claim = Claim.from_dict(payload)
    updated_claim.claim_id = claim_id

    if updated_claim.policy_id:
        policy_data = fetch_policy(updated_claim.policy_id)
        if not policy_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La police '{updated_claim.policy_id}' n'existe pas dans policy-service.",
            )
        evaluate_claim_with_policy(updated_claim, policy_data)

    claims_db[claim_id] = updated_claim
    return updated_claim.to_dict()


@router.patch("/{claim_id}/status", summary="Modifier le statut d'un sinistre")
def update_claim_status(
    claim_id: str,
    new_status: str = Query(..., alias="status", description="Nouveau statut : PENDING, APPROVED, REJECTED"),
    rejection_reason: Optional[str] = Query(None, alias="rejectionReason", description="Motif en cas de rejet"),
) -> Dict[str, Any]:
    claim = claims_db.get(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sinistre '{claim_id}' introuvable.",
        )
    claim.status = new_status.upper()
    if rejection_reason is not None:
        claim.rejection_reason = rejection_reason
    return claim.to_dict()


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un sinistre")
def delete_claim(claim_id: str) -> None:
    if claim_id not in claims_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sinistre '{claim_id}' introuvable.",
        )
    del claims_db[claim_id]

