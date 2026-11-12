from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from models.policy import Policy
from schemas.policy_schema import (
    PolicyCreate,
    PolicyResponse,
    PolicyStatus,
    PolicyUpdate,
    PolicyValidityResponse,
)

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


def _to_response(policy: Policy) -> PolicyResponse:
    return PolicyResponse.model_validate(policy)


def _get_or_404(policy_id: str) -> Policy:
    policy = policies_db.get(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Police d'assurance '{policy_id}' introuvable.",
        )
    return policy


@router.get("", response_model=List[PolicyResponse], summary="Lister toutes les polices d'assurance")
def get_all_policies(
    status_filter: Optional[PolicyStatus] = Query(None, alias="status", description="Filtrer par statut"),
    client_id: Optional[str] = Query(None, alias="clientId", description="Filtrer par identifiant client"),
):
    results = list(policies_db.values())
    if status_filter:
        results = [p for p in results if p.status == status_filter.value]
    if client_id:
        results = [p for p in results if p.client_id == client_id]
    return [_to_response(p) for p in results]


@router.get("/{policy_id}", response_model=PolicyResponse, summary="Récupérer une police par son ID")
def get_policy_by_id(policy_id: str):
    return _to_response(_get_or_404(policy_id))


@router.get(
    "/{policy_id}/validity",
    response_model=PolicyValidityResponse,
    summary="Vérifier si une police couvre une date donnée (utilisé par le claim-service)",
)
def check_policy_validity(
    policy_id: str,
    check_date: Optional[date] = Query(None, alias="date", description="Date du sinistre (défaut : aujourd'hui)"),
):
    policy = _get_or_404(policy_id)
    check_date = check_date or date.today()

    reasons: List[str] = []
    if policy.status != PolicyStatus.ACTIVE.value:
        reasons.append(f"La police n'est pas active (statut : {policy.status}).")
    if not policy.start_date or not policy.end_date:
        reasons.append("Les dates de couverture de la police ne sont pas définies.")
    elif check_date < policy.start_date:
        reasons.append(f"La police n'est pas encore en vigueur (début : {policy.start_date.isoformat()}).")
    elif check_date > policy.end_date:
        reasons.append(f"La police a expiré (fin : {policy.end_date.isoformat()}).")

    return PolicyValidityResponse(
        policy_id=policy.policy_id,
        check_date=check_date,
        valid=not reasons,
        status=policy.status,
        coverage_type=policy.coverage_type,
        coverage_limit=policy.coverage_limit,
        deductible=policy.deductible,
        reasons=reasons,
    )


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle police",
)
def create_policy(payload: PolicyCreate):
    if payload.policy_id in policies_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une police avec l'ID '{payload.policy_id}' existe déjà.",
        )
    policy = Policy(**payload.model_dump())
    policies_db[policy.policy_id] = policy
    return _to_response(policy)


@router.put("/{policy_id}", response_model=PolicyResponse, summary="Mettre à jour une police existante")
def update_policy(policy_id: str, payload: PolicyUpdate):
    _get_or_404(policy_id)
    updated_policy = Policy(policy_id=policy_id, **payload.model_dump())
    policies_db[policy_id] = updated_policy
    return _to_response(updated_policy)


@router.patch("/{policy_id}/status", response_model=PolicyResponse, summary="Modifier le statut d'une police")
def update_policy_status(
    policy_id: str,
    new_status: PolicyStatus = Query(..., alias="status", description="Nouveau statut"),
):
    policy = _get_or_404(policy_id)
    policy.status = new_status.value
    return _to_response(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer une police")
def delete_policy(policy_id: str) -> None:
    _get_or_404(policy_id)
    del policies_db[policy_id]
