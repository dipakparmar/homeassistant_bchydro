"""BC Hydro API types."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, TypedDict, Any

@dataclass
class BCHydroRates:
    """Rate information."""
    step1_rate: float
    step2_rate: float
    threshold: float

@dataclass
class BCHydroInterval:
    """Time interval for consumption data."""
    start: datetime
    end: datetime
    billing_period_end: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"BCHydroInterval(start={self.start}, end={self.end})"

@dataclass
class BCHydroDailyElectricity:
    """Daily electricity usage data."""
    consumption: float
    cost: float
    interval: BCHydroInterval
    is_estimate: bool = False

class BCHydroAccountData(TypedDict):
    """Account details returned from the account JSON response."""
    accountId: str
    firstName: str
    lastName: str
    accountStatus: str
    address: Dict[str, Any]

@dataclass
class BCHydroAccount:
    """Account information."""
    account_id: str
    first_name: str
    last_name: str
    status: str
    address: Dict[str, Any]

    @classmethod
    def from_json(cls, data: BCHydroAccountData) -> "BCHydroAccount":
        """Create account from JSON response."""
        return cls(
            account_id=data["accountId"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            status=data["accountStatus"],
            address=data["address"],
        )

@dataclass
class BCHydroDailyUsage:
    """Daily usage data."""
    account: BCHydroAccount
    interval: BCHydroInterval
    rates: BCHydroRates
    electricity: List[BCHydroDailyElectricity]
