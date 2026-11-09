from datetime import date
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Body, HTTPException, Query, status
from models.policy import Policy

router = APIRouter(prefix="/policies", tags=["Policies"])

# Base de données en mémoire (Phase 1 : exemples utilisant @Builder et le constructeur simplifié à 4 champs)
policies_db: Dict[str, Policy] = {
    "POL-2026-001": (
        Policy.builder()
        .policy_id("POL-2026-001")
        .client_name("Jean Dupont")
        .vehicle_model("Peugeot 208")
        .premium_amount(550.0)
        .client_id("CLI-001")
        .license_plate("AB-123-CD")
        .status("ACTIVE")
        .coverage_type("TOUS_RISQUES")
        .coverage_limit(25000.0)
        .deductible(300.0)
        .start_date(date(2026, 1, 1))
        .end_date(date(2026, 12, 31))
        .build()
    ),
    # Constructeur simplifié avec uniquement les 4 champs de base (status = "ACTIVE" par défaut)
    "POL-2026-002": Policy("POL-2026-002", "Marie Martin", "Renault Clio V", 420.0),
}


@router.get("", summary="Lister toutes les polices d'assurance")
def get_all_policies(
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut (ex: ACTIVE)"),
    client_id: Optional[str] = Query(None, alias="clientId", description="Filtrer par identifiant client"),
) -> List[Dict[str, Any]]:
    results = list(policies_db.values())
    if status_filter:
        results = [p for p in results if p.status.upper() == status_filter.upper()]
    if client_id:
        results = [p for p in results if p.client_id == client_id]
    return [p.to_dict() for p in results]


@router.get("/{policy_id}", summary="Récupérer une police par son ID")
def get_policy_by_id(policy_id: str) -> Dict[str, Any]:
    policy = policies_db.get(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Police d'assurance '{policy_id}' introuvable.",
        )
    return policy.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Créer une nouvelle police")
def create_policy(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    policy = Policy.from_dict(payload)
    if not policy.policy_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le champ 'policyId' (ou 'policy_id') est obligatoire.",
        )
    if policy.policy_id in policies_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une police avec l'ID '{policy.policy_id}' existe déjà.",
        )
    policies_db[policy.policy_id] = policy
    return policy.to_dict()


@router.put("/{policy_id}", summary="Mettre à jour une police existante")
def update_policy(policy_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if policy_id not in policies_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Police d'assurance '{policy_id}' introuvable.",
        )
    updated_policy = Policy.from_dict(payload)
    updated_policy.policy_id = policy_id
    policies_db[policy_id] = updated_policy
    return updated_policy.to_dict()


@router.patch("/{policy_id}/status", summary="Modifier le statut d'une police")
def update_policy_status(
    policy_id: str,
    new_status: str = Query(..., alias="status", description="Nouveau statut : ACTIVE, SUSPENDED, EXPIRED"),
) -> Dict[str, Any]:
    policy = policies_db.get(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Police d'assurance '{policy_id}' introuvable.",
        )
    policy.status = new_status.upper()
    return policy.to_dict()


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer une police")
def delete_policy(policy_id: str) -> None:
    if policy_id not in policies_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Police d'assurance '{policy_id}' introuvable.",
        )
    del policies_db[policy_id]

