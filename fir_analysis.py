from __future__ import annotations
import re
from typing import Any


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" .,:;\t\r\n")


def _split_values(value: str) -> list[str]:
    value = _clean(value)
    if not value:
        return []
    parts = re.split(r",|;|\band\b", value, flags=re.I)
    return list(dict.fromkeys(_clean(p) for p in parts if _clean(p)))


def _normal(text: str) -> str:
    # PDF extraction often collapses line breaks into spaces.
    return _clean(text)


def _line_fields(text: str) -> list[tuple[str, str]]:
    """Return colon-delimited fields from both normal and PDF-extracted text."""
    raw = (text or "").replace("\r", "\n")
    # Preserve explicit lines first; PDF extraction can also place multiple fields
    # on one line, so split those using known labels below.
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.split("\n")]
    return [(line, line) for line in lines if line]


def _find_label_value(text: str, labels: list[str]) -> str:
    """Extract one labelled value, preferring exact line/field boundaries."""
    s = text or ""
    labels = sorted(labels, key=len, reverse=True)
    label_alt = "|".join(re.escape(x) for x in labels)

    # First handle ordinary FIR text where every field is on its own line.
    for line in s.replace("\r", "\n").split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        m = re.match(rf"^(?:{label_alt})\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            return _clean(m.group(1))

    # Handle PDF extraction where several labelled fields may share a line.
    stop_labels = sorted(set(labels + [
        "Police Station", "District", "State", "FIR No.", "FIR No", "FIR Number",
        "FIR ID", "Date of FIR", "FIR Date", "Incident Date", "Date", "Time",
        "Complainant / Informant Name", "Complainant", "Informant", "Name", "Age",
        "Address", "Contact", "Date and Time of Occurrence", "Place of Occurrence",
        "Location", "Locations", "Place of Incident", "Vehicle", "Vehicles",
        "Vehicle No", "Registration Number", "Phone", "Phone Number", "Mobile",
        "Mobile Number", "Account", "Account Number", "Bank Account",
        "Persons Mentioned", "Persons", "Suspects", "Individuals", "People",
        "Subject", "Title", "Case ID", "Case No", "Case Number"
    ]), key=len, reverse=True)
    stop_alt = "|".join(re.escape(x) for x in stop_labels)
    m = re.search(rf"(?:{label_alt})\s*:\s*(.*?)(?=\s+(?:{stop_alt})\s*:|$)", re.sub(r"\s+", " ", s), re.I)
    return _clean(m.group(1)) if m else ""


def _find_all_label_values(text: str, labels: list[str]) -> list[str]:
    """Extract one or more comma/semicolon separated values from labelled FIR fields."""
    s = text or ""
    labels = sorted(labels, key=len, reverse=True)
    label_alt = "|".join(re.escape(x) for x in labels)
    results: list[str] = []

    # Normal line-based FIRs: this is the most reliable path and avoids treating
    # words such as 'Location X' as a new field.
    for line in s.replace("\r", "\n").split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        m = re.match(rf"^(?:{label_alt})\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            results.extend(_split_values(m.group(1)))

    # PDF fallback: locate labels in a normalized stream and stop at the next
    # known colon-delimited FIR label.
    normalized = re.sub(r"\s+", " ", s)
    stop_labels = sorted(set([
        "Police Station", "District", "State", "FIR No.", "FIR No", "FIR Number",
        "FIR ID", "Date of FIR", "FIR Date", "Incident Date", "Date", "Time",
        "Complainant / Informant Name", "Complainant", "Informant", "Name", "Age",
        "Address", "Contact", "Date and Time of Occurrence", "Place of Occurrence",
        "Location", "Locations", "Place of Incident", "Reported Incident Area",
        "Primary Location", "Related Location", "Vehicle", "Vehicles", "Vehicle No",
        "Registration Number", "Phone", "Phone Number", "Mobile", "Mobile Number",
        "Account", "Account Number", "Bank Account", "Persons Mentioned", "Persons",
        "Suspects", "Individuals", "People", "Subject", "Title", "Case ID", "Case No",
        "Case Number"
    ]), key=len, reverse=True)
    stop_alt = "|".join(re.escape(x) for x in stop_labels)
    for label in labels:
        pattern = rf"{re.escape(label)}\s*:\s*(.*?)(?=\s+(?:{stop_alt})\s*:|$)"
        for m in re.finditer(pattern, normalized, re.I):
            results.extend(_split_values(m.group(1)))

    return list(dict.fromkeys(x for x in (_clean(v) for v in results) if x))


def analyze_fir_text(text: str, graph: Any | None = None, alerts: list[dict] | None = None) -> dict:
    if not text or not text.strip():
        raise ValueError("FIR text cannot be empty")
    text = text[:100_000]

    fir_number = _find_label_value(text, ["FIR No.", "FIR No", "FIR Number", "FIR ID"])
    case_id = _find_label_value(text, ["Case ID", "Case No", "Case Number"])
    date = _find_label_value(text, ["Date of FIR", "FIR Date", "Incident Date"])
    if not date:
        # If the document has only a generic Date field, use it as a fallback.
        date = _find_label_value(text, ["Date"])
    if not fir_number:
        m = re.search(r"FIR\s*No\.?\s*:\s*([^\s]+)", _normal(text), re.I)
        fir_number = _clean(m.group(1)) if m else ""
    if not case_id:
        m = re.search(r"\bCASE[-\s]?\d{1,6}\b", text, re.I)
        case_id = m.group(0).upper().replace(" ", "-") if m else "FIR-UNASSIGNED"

    # Handle the common "Complainant / Informant Name:" form first.
    complainant = _find_label_value(text, [
        "Complainant / Informant Name", "Complainant", "Informant"
    ])

    persons = _find_all_label_values(text, ["Persons Mentioned", "Persons", "Suspects", "Individuals", "People"])
    if complainant and complainant not in persons:
        persons.insert(0, complainant)

    locations = _find_all_label_values(text, [
        "Location", "Locations", "Place of Incident", "Place of Occurrence",
        "Reported Incident Area", "Primary Location", "Related Location"
    ])
    vehicles = _find_all_label_values(text, ["Vehicle", "Vehicles", "Vehicle No", "Registration Number"])
    phones = _find_all_label_values(text, ["Phone", "Phone Number", "Mobile", "Mobile Number", "Contact"])
    accounts = _find_all_label_values(text, ["Account", "Account Number", "Bank Account"])

    # Fallbacks for identifiers commonly present in PDFs.
    phones += re.findall(r"(?:\+91[-\s]?)?(?:\d{5}\s\d{5}|[6-9]\d{9})", text)
    vehicles += re.findall(r"\bV(?:EHICLE)?[-\s]?\d{1,5}\b", text, re.I)
    accounts += re.findall(r"\bACC[-\s]?\d{1,8}\b", text, re.I)
    phones = list(dict.fromkeys(_clean(x) for x in phones if _clean(x)))
    vehicles = list(dict.fromkeys(_clean(x).upper() for x in vehicles if _clean(x)))
    accounts = list(dict.fromkeys(_clean(x).upper().replace(" ", "-") for x in accounts if _clean(x)))

    relationships = []
    for person in persons:
        for location in locations:
            relationships.append({"source": person, "target": location, "relationship": "MENTIONED_AT"})
        for vehicle in vehicles:
            relationships.append({"source": person, "target": vehicle, "relationship": "ASSOCIATED_WITH"})
        for phone in phones:
            relationships.append({"source": person, "target": phone, "relationship": "PHONE_REFERENCE"})
        for account in accounts:
            relationships.append({"source": person, "target": account, "relationship": "ACCOUNT_REFERENCE"})

    matched_entities = []
    if graph is not None:
        wanted = {str(x).strip().lower() for x in persons + locations + vehicles + phones + accounts}
        for node, data in graph.nodes(data=True):
            node_id = str(node)
            node_name = str(data.get("name", node))
            if node_id.lower() in wanted or node_name.lower() in wanted:
                matched_entities.append({"id": node_id, "name": node_name, "type": data.get("node_type", "unknown")})

    leads = []
    if len(persons) >= 2:
        leads.append({"title": "Multiple persons referenced", "detail": f"{len(persons)} person references were extracted for investigator review."})
    if vehicles:
        leads.append({"title": "Vehicle reference detected", "detail": "Vehicle identifiers can be compared with synthetic vehicle records."})
    if phones:
        leads.append({"title": "Communication identifier detected", "detail": "Phone references can be compared with synthetic communication records."})
    if accounts:
        leads.append({"title": "Financial identifier detected", "detail": "Account references can be compared with synthetic transaction records."})
    if locations:
        leads.append({"title": "Location reference detected", "detail": "Location references can be compared with synthetic location records."})

    return {
        "case_id": case_id,
        "fir_number": fir_number,
        "date": date,
        "title": _find_label_value(text, ["Title", "Subject"]) or "Synthetic FIR Analysis",
        "extraction_method": "RULE-BASED NLP",
        "entity_count": len(persons) + len(locations) + len(vehicles) + len(phones) + len(accounts),
        "complainant": complainant,
        "persons": persons,
        "locations": locations,
        "vehicles": vehicles,
        "phones": phones,
        "accounts": accounts,
        "extracted": {
            "persons": persons,
            "locations": locations,
            "vehicles": vehicles,
            "phones": phones,
            "accounts": accounts,
        },
        "relationships": relationships,
        "matched_entities": matched_entities,
        "analytical_leads": leads,
        "case_created": False,
        "note": "Synthetic demonstration only. Extraction and correlation are analytical aids and do not establish criminal activity or guilt."
    }
