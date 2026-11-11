from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any


@dataclass
class Claim:
    """
    Équivalent Python de la classe Java Claim avec :
    - @Data (@dataclass génère getters/setters, __eq__, __repr__)
    - @NoArgsConstructor (tous les champs ont une valeur par défaut)
    - @AllArgsConstructor (constructeur avec tous les champs)
    - Constructeur simplifié à 4 arguments : Claim(claim_id, policy_id, description, claimed_amount)
    - @Builder via Claim.builder()
    """

    # --- Données de base (les 4 premiers champs permettent le constructeur simplifié) ---
    claim_id: Optional[str] = None
    policy_id: Optional[str] = None          # Référence vers la police dans policy-service
    description: Optional[str] = None        # Description des circonstances du sinistre
    claimed_amount: float = 0.0              # Montant estimé des dommages réclamé par l'assuré

    # --- Données enrichies et cycle de vie du sinistre ---
    approved_amount: float = 0.0             # Montant retenu après application de la franchise et du plafond
    status: str = "PENDING"                  # Ex: "PENDING", "APPROVED", "REJECTED"
    incident_date: Optional[date] = None     # Date de survenance du sinistre
    declaration_date: Optional[date] = None  # Date de déclaration du sinistre
    rejection_reason: Optional[str] = None   # Motif en cas de rejet (ex: police expirée ou suspendue)

    @staticmethod
    def builder() -> "ClaimBuilder":
        """Point d'entrée du pattern @Builder."""
        return ClaimBuilder()

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'objet Claim en dictionnaire JSON-compatible (camelCase)."""
        return {
            "claimId": self.claim_id,
            "policyId": self.policy_id,
            "description": self.description,
            "claimedAmount": self.claimed_amount,
            "approvedAmount": self.approved_amount,
            "status": self.status,
            "incidentDate": self.incident_date.isoformat() if self.incident_date else None,
            "declarationDate": self.declaration_date.isoformat() if self.declaration_date else None,
            "rejectionReason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        """Désérialise un dictionnaire (camelCase ou snake_case) en instance Claim."""
        incident_raw = data.get("incidentDate") or data.get("incident_date")
        declaration_raw = data.get("declarationDate") or data.get("declaration_date")

        return cls(
            claim_id=data.get("claimId") or data.get("claim_id"),
            policy_id=data.get("policyId") or data.get("policy_id"),
            description=data.get("description"),
            claimed_amount=float(data.get("claimedAmount", data.get("claimed_amount", 0.0))),
            approved_amount=float(data.get("approvedAmount", data.get("approved_amount", 0.0))),
            status=data.get("status", "PENDING"),
            incident_date=date.fromisoformat(incident_raw) if isinstance(incident_raw, str) else incident_raw,
            declaration_date=(
                date.fromisoformat(declaration_raw)
                if isinstance(declaration_raw, str)
                else (declaration_raw or date.today())
            ),
            rejection_reason=data.get("rejectionReason") or data.get("rejection_reason"),
        )


class ClaimBuilder:
    """Implémentation fluide du pattern @Builder de Lombok pour Claim."""

    def __init__(self) -> None:
        self._claim = Claim()

    def claim_id(self, value: str) -> "ClaimBuilder":
        self._claim.claim_id = value
        return self

    def policy_id(self, value: str) -> "ClaimBuilder":
        self._claim.policy_id = value
        return self

    def description(self, value: str) -> "ClaimBuilder":
        self._claim.description = value
        return self

    def claimed_amount(self, value: float) -> "ClaimBuilder":
        self._claim.claimed_amount = value
        return self

    def approved_amount(self, value: float) -> "ClaimBuilder":
        self._claim.approved_amount = value
        return self

    def status(self, value: str) -> "ClaimBuilder":
        self._claim.status = value
        return self

    def incident_date(self, value: date) -> "ClaimBuilder":
        self._claim.incident_date = value
        return self

    def declaration_date(self, value: date) -> "ClaimBuilder":
        self._claim.declaration_date = value
        return self

    def rejection_reason(self, value: Optional[str]) -> "ClaimBuilder":
        self._claim.rejection_reason = value
        return self

    def build(self) -> Claim:
        return self._claim

