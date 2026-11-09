from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any


@dataclass
class Policy:
    """
    Équivalent Python de la classe Java Policy avec :
    - @Data (@dataclass génère getters/setters, __eq__, __repr__)
    - @NoArgsConstructor (tous les champs ont une valeur par défaut)
    - @AllArgsConstructor (constructeur avec tous les champs)
    - Constructeur simplifié à 4 arguments : Policy(policy_id, client_name, vehicle_model, premium_amount)
    - @Builder via Policy.builder()
    """

    # --- Données de base demandées (les 4 premiers champs permettent aussi le constructeur simplifié) ---
    policy_id: Optional[str] = None
    client_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    premium_amount: float = 0.0

    # --- Données recommandées pour l'interaction avec les autres microservices ---
    client_id: Optional[str] = None          # Lien avec un microservice Client / Notification
    license_plate: Optional[str] = None      # Plaque d'immatriculation unique du véhicule assuré
    status: str = "ACTIVE"                   # Ex: "ACTIVE", "SUSPENDED", "EXPIRED" (vérifié par le service Sinistres)
    coverage_type: Optional[str] = None      # Ex: "TIERS", "TOUS_RISQUES"
    coverage_limit: float = 0.0              # Plafond maximal de remboursement en cas de sinistre
    deductible: float = 0.0                  # Franchise à déduire lors d'une indemnisation
    start_date: Optional[date] = None        # Date de début de validité du contrat
    end_date: Optional[date] = None          # Date de fin de validité du contrat

    @staticmethod
    def builder() -> "PolicyBuilder":
        """Point d'entrée du pattern @Builder."""
        return PolicyBuilder()

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'objet Policy en dictionnaire JSON-compatible (camelCase)."""
        return {
            "policyId": self.policy_id,
            "clientName": self.client_name,
            "vehicleModel": self.vehicle_model,
            "premiumAmount": self.premium_amount,
            "clientId": self.client_id,
            "licensePlate": self.license_plate,
            "status": self.status,
            "coverageType": self.coverage_type,
            "coverageLimit": self.coverage_limit,
            "deductible": self.deductible,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "endDate": self.end_date.isoformat() if self.end_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Désérialise un dictionnaire (camelCase ou snake_case) en instance Policy."""
        start_raw = data.get("startDate") or data.get("start_date")
        end_raw = data.get("endDate") or data.get("end_date")

        return cls(
            policy_id=data.get("policyId") or data.get("policy_id"),
            client_name=data.get("clientName") or data.get("client_name"),
            vehicle_model=data.get("vehicleModel") or data.get("vehicle_model"),
            premium_amount=float(data.get("premiumAmount", data.get("premium_amount", 0.0))),
            client_id=data.get("clientId") or data.get("client_id"),
            license_plate=data.get("licensePlate") or data.get("license_plate"),
            status=data.get("status", "ACTIVE"),
            coverage_type=data.get("coverageType") or data.get("coverage_type"),
            coverage_limit=float(data.get("coverageLimit", data.get("coverage_limit", 0.0))),
            deductible=float(data.get("deductible", 0.0)),
            start_date=date.fromisoformat(start_raw) if isinstance(start_raw, str) else start_raw,
            end_date=date.fromisoformat(end_raw) if isinstance(end_raw, str) else end_raw,
        )


class PolicyBuilder:
    """Implémentation fluide du pattern @Builder de Lombok pour Policy."""

    def __init__(self) -> None:
        self._policy = Policy()

    def policy_id(self, value: str) -> "PolicyBuilder":
        self._policy.policy_id = value
        return self

    def client_name(self, value: str) -> "PolicyBuilder":
        self._policy.client_name = value
        return self

    def vehicle_model(self, value: str) -> "PolicyBuilder":
        self._policy.vehicle_model = value
        return self

    def premium_amount(self, value: float) -> "PolicyBuilder":
        self._policy.premium_amount = value
        return self

    def client_id(self, value: str) -> "PolicyBuilder":
        self._policy.client_id = value
        return self

    def license_plate(self, value: str) -> "PolicyBuilder":
        self._policy.license_plate = value
        return self

    def status(self, value: str) -> "PolicyBuilder":
        self._policy.status = value
        return self

    def coverage_type(self, value: str) -> "PolicyBuilder":
        self._policy.coverage_type = value
        return self

    def coverage_limit(self, value: float) -> "PolicyBuilder":
        self._policy.coverage_limit = value
        return self

    def deductible(self, value: float) -> "PolicyBuilder":
        self._policy.deductible = value
        return self

    def start_date(self, value: date) -> "PolicyBuilder":
        self._policy.start_date = value
        return self

    def end_date(self, value: date) -> "PolicyBuilder":
        self._policy.end_date = value
        return self

    def build(self) -> Policy:
        return self._policy

