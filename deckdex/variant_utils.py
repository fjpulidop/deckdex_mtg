from typing import Optional


def derive_variant_label(
    finish: str,
    promo_types: Optional[str],
    frame_effects: Optional[str],
    border_color: Optional[str],
) -> str:
    """
    Derive a human-readable variant label from Scryfall treatment fields.
    Priority order: serialized > etched > showcase > extendedart > borderless > foil > regular.
    """
    pt = (promo_types or "").lower()
    fe = (frame_effects or "").lower()
    bc = (border_color or "").lower()
    fo = (finish or "nonfoil").lower()

    is_foil = fo == "foil"
    foil_suffix = " Foil" if is_foil else ""

    if "serialized" in pt:
        return f"Serialized{foil_suffix}"
    if "etched" in fe or fo == "etched":
        return "Etched Foil"
    if "showcase" in fe:
        return f"Showcase{foil_suffix}"
    if "extendedart" in fe:
        return f"Extended Art{foil_suffix}"
    if bc == "borderless":
        return f"Borderless{foil_suffix}"
    if is_foil:
        return "Foil"
    return "Regular"
