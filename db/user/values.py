"""Values of the reviewable data stored in user.sqlite, and the hash of a proposal (RN-18)."""

import hashlib
import json

# A boolean (a mechanic, whether a form exists or can arrive) or the Pokémon of a key battle.
type ConfirmedValue = bool | list[str]


def value_hash(proposal: ConfirmedValue | None) -> str:
    """Stable hash of a proposed value; ``None`` is the proposal of a pending value.

    A confirmation stores the hash of the proposal it answered. If a later load proposes a
    different value, the hashes differ and the user is asked again (RF-15).
    """
    encoded = json.dumps(proposal, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
