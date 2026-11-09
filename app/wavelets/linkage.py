"""
Helpers for server-owned wavelet linkage metadata.
"""

from typing import Any
from typing import Literal
from uuid import UUID

from core.models import Domain
from rest_framework import serializers


def add_linkage_metadata(
    validated_data: dict[str, Any], request: Any
) -> dict[str, Any]:
    """
    Stamp authenticated ownership and classify the document's initial link state.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        raise serializers.ValidationError("Authentication required.")

    data = {
        **validated_data,
        "user_id": str(user.pk),
    }
    if data.get("domain_id"):
        data["link_status"] = "linked"
    elif data.get("domain_session_id"):
        data["link_status"] = "pending"
    else:
        data["link_status"] = ""

    return data


def resolve_domain_id(
    user_id: UUID, domain_session_id: str
) -> tuple[UUID | None, Literal["matched", "missing", "ambiguous"]]:
    """Resolve an exact visit hint within a single participant's records."""
    matches = list(
        Domain.objects.filter(
            user_id=user_id, domain_session_id=domain_session_id
        ).values_list("id", flat=True)[:2]
    )
    if not matches:
        return None, "missing"
    if len(matches) > 1:
        return None, "ambiguous"
    return matches[0], "matched"
