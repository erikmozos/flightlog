"""
Heurísticas para extraer datos de un OFP / SimBrief en texto plano.
SimBrief tiene varios formatos; tratamos etiquetas conocidas y líneas con pares ICAO.
"""

from __future__ import annotations

import re
from datetime import time, timedelta
from typing import Any

_ICAO_WORD = r"\b([A-Z]{4})\b"
# Tokens de 4 letras muy frecuentes en texto OFP/plan que no son códigos de aeródromo.
_SKIP_ICAO_TOKENS = frozenset(
    {
        "PLAN",
        "TEXT",
        "WIND",
        "FUEL",
        "OFP",
        "AUTO",
        "GPS",
        "RWY",
        "SID",
        "STAR",
        "TOC",
        "TOD",
        "RNAV",
        "NIL",
        "NONE",
        "UTC",
        "FREQ",
        "ATIS",
        "DIST",
        "NOTA",
        "META",
        "AREA",
        "GRID",
        "TRUE",
        "TIME",
        "DATE",
        "LOAD",
        "ZERO",
        "FULL",
        "HALF",
        "WILL",
        "TAKE",
    }
)


def _capture_after_label(lines: list[str], labels: tuple[str, ...]) -> str | None:
    """Valor en la misma línea después de LABEL o similar (KEY: VALUE)."""
    lbl_join = "|".join(re.escape(x) for x in labels)
    pat = re.compile(rf"\b(?:{lbl_join})\b\s*[.:]?\s*{_ICAO_WORD}", re.IGNORECASE)
    for ln in lines:
        m = pat.search(ln)
        if m:
            raw = (m.group(1) or "").upper()
            if len(raw) == 4:
                return raw
    # Formato LABEL ... VALUE donde VALUE más al final
    for ln in lines:
        u = ln.upper().strip()
        if not u:
            continue
        hit = False
        for lb in labels:
            if lb in u.replace(" ", "") or lb in u:
                hit = True
                break
        if not hit:
            continue
        m2 = re.search(_ICAO_WORD, u)
        if m2:
            return m2.group(1).upper()
    return None


def _paired_from_to(lines: list[str]) -> tuple[str | None, str | None]:
    """FROM/TO / DEP ARR / ORIGIN DEST en líneas combinadas."""
    dep = arrival = None
    for ln in lines:
        up = ln.upper().replace("\t", " ")
        combined = up
        pair = None
        for pat in (
            r"\bORIGIN\D+([A-Z]{4})\s+.*?\bDEST(?:INATION)?\D+([A-Z]{4})\b",
            r"\bFROM\D+([A-Z]{4})\s+.*?\bTO\D+([A-Z]{4})\b",
            r"\bDEP(?:ART)?\w*\D+([A-Z]{4})\s+.*?\bARR(?:IVAL)?\D+([A-Z]{4})\b",
            r"\b([A-Z]{4})\s+[/-]\s+([A-Z]{4})\b",
        ):
            m = re.search(pat, combined, flags=re.DOTALL)
            if m:
                pair = (m.group(1), m.group(2))
                break
        if pair:
            dep, arrival = pair[0], pair[1]
            break
    return dep, arrival


def _route_line(lines: list[str]) -> str | None:
    for ln in lines:
        lu = ln.strip()
        mu = ln.upper().strip()
        if re.match(r"ROUTE\b", mu):
            idx = ln.upper().find("ROUTE")
            rest = lu[idx + len("ROUTE") :].lstrip(": \t-")
            if rest:
                return rest.strip()
    return None


def _two_icao_from_block(text_upper: str) -> tuple[str | None, str | None]:
    """
    Primer y segundo ICAO típicos cuando aparecen tras «FLIGHT PLAN» o bloque plano.
    Heurística: tomar los dos primeros token ICAO distintos en orden de aparición.
    """
    found: list[str] = []
    for m in re.finditer(_ICAO_WORD, text_upper):
        code = m.group(1)
        if code in _SKIP_ICAO_TOKENS:
            continue
        if code not in found:
            found.append(code)
        if len(found) >= 2:
            break
    if len(found) >= 2:
        return found[0], found[1]
    return None, None


def _parse_time_value(s: str) -> time | None:
    s = s.strip().upper()
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})(?:\s*:\s*(\d{2}))?", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3)) if m.group(3) else 0
        if 0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59:
            return time(h, mi, sec)
    m2 = re.search(r"\b(\d{3,4})Z?\b", s)
    if m2:
        raw = m2.group(1)
        if len(raw) == 4:
            h, mi = int(raw[:2]), int(raw[2:])
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return time(h, mi, 0)
    return None


def _find_departure_time(lines: list[str]) -> time | None:
    labels = ("ETD", "STD", "DEP TIME", "DEPTIME", "DEPARTURE TIME")
    lbl = "|".join(re.escape(x.replace(" ", r"\s+")) for x in labels)
    pat = re.compile(rf"\b(?:{lbl})\b\s*[.:]?\s*(.+)$", re.IGNORECASE)
    for ln in lines:
        m = pat.search(ln.strip())
        if m:
            t = _parse_time_value(m.group(1))
            if t:
                return t
    return None


def _find_duration(lines: list[str]) -> timedelta | None:
    labels = ("EET", "ETE", "ENROUTE TIME", "EN ROUTE TIME", "FLIGHT TIME")
    for ln in lines:
        u = ln.upper()
        if not any(lb in u for lb in labels):
            continue
        # HH:MM o H:MM
        m = re.search(r"(\d+)\s*:\s*(\d+)(?:\s*:\s*(\d+))?", ln)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            sec = int(m.group(3)) if m.group(3) else 0
            return timedelta(hours=h, minutes=mi, seconds=sec)
        # "1H35M" / "1h 35m"
        m2 = re.search(r"(\d+)\s*H\s*(\d+)\s*M", ln, re.IGNORECASE)
        if m2:
            return timedelta(hours=int(m2.group(1)), minutes=int(m2.group(2)))
    return None


def _find_flight_number(lines: list[str]) -> str | None:
    labels = ("FLIGHT", "FLT", "CALLSIGN")
    pat = re.compile(
        rf"\b(?:{'|'.join(re.escape(x) for x in labels)})\b\s*[.:]?\s*([A-Z0-9][A-Z0-9\- ]{{1,18}})",
        re.IGNORECASE,
    )
    for ln in lines:
        m = pat.search(ln.strip())
        if m:
            val = re.sub(r"\s+", " ", m.group(1).strip())
            if val:
                return val[:20]
    return None


def _valid_aircraft_type_token(tok: str) -> bool:
    """Evita falsos positivos tipo NOTAM «…AIRCRAFT WILL …». Los OACI tipo prácticamente llevan dígito (A321…)."""
    c = (tok or "").strip().upper()
    if len(c) < 2 or len(c) > 16:
        return False
    if c in _SKIP_ICAO_TOKENS:
        return False
    return bool(re.search(r"\d", c))


def _find_aircraft_type(lines: list[str]) -> str | None:
    """Designadores tipo suelen llevar dígitos (B738, A321…). No confundir con texto tras la palabra AIRCRAFT."""
    pat = re.compile(
        r"\b(?:AIRCRAFT|ACFT|TYPE|ACTYPE|TYP)\b\s*[.:]?\s*([A-Z][A-Z0-9\-]{2,14})\b",
        re.IGNORECASE,
    )
    for ln in lines:
        m = pat.search(ln.strip())
        if not m:
            continue
        cand = m.group(1).strip().upper()[:16]
        if _valid_aircraft_type_token(cand):
            return cand

    # Fallback estable: patrón ICAO FPL típico «-A321/M-» o «-B738/H-».
    fpl = "\n".join(lines)
    m2 = re.search(r"(?:\s+-|^)\s*-\s*([A-Z]{1,3}\d[A-Z0-9]{0,11})\s*/\s*[A-Z]", fpl, re.IGNORECASE | re.MULTILINE)
    if m2:
        cand2 = m2.group(1).strip().upper()
        if _valid_aircraft_type_token(cand2):
            return cand2[:16]
    return None


def parse_simbrief_text(raw_text: str) -> dict[str, Any]:
    """
    Devuelve claves con None o "" cuando no hay dato.
    planned_departure_time: datetime.time o None
    estimated_flight_time: datetime.timedelta o None
    """
    out: dict[str, Any] = {
        "flight_number": None,
        "departure_icao": None,
        "arrival_icao": None,
        "alternate_icao": None,
        "aircraft_icao": None,
        "route": "",
        "planned_departure_time": None,
        "estimated_flight_time": None,
    }
    if not raw_text or not str(raw_text).strip():
        return out

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    dep = _capture_after_label(lines, ("ORIGIN", "DEP", "FROM", "ADEP"))
    arr = _capture_after_label(lines, ("DEST", "DESTINATION", "ARR", "TO", "ADES"))
    if not dep or not arr:
        d2, a2 = _paired_from_to(lines)
        dep = dep or d2
        arr = arr or a2
    if not dep or not arr:
        d3, a3 = _two_icao_from_block(text.upper())
        dep = dep or d3
        arr = arr or a3

    out["departure_icao"] = dep
    out["arrival_icao"] = arr

    # Evitar la etiqueta suelta «ALT» (altitud / nivel de vuelo): suele dar falsos positivos.
    altn = _capture_after_label(lines, ("ALTN", "ALTERNATE", "DIV"))
    out["alternate_icao"] = altn

    out["aircraft_icao"] = _find_aircraft_type(lines)
    out["flight_number"] = _find_flight_number(lines)
    out["planned_departure_time"] = _find_departure_time(lines)
    out["estimated_flight_time"] = _find_duration(lines)

    route = _route_line(lines)
    if not route and dep and arr:
        # Heurística: línea larga con waypoints entre cabeceras de salida/llegada
        between: list[str] = []
        started = False
        for ln in lines:
            u = ln.upper().strip()
            if not u:
                continue
            if dep in u and arr in u and len(u) > 12:
                between.append(ln.strip())
                started = True
                continue
            if started:
                if re.match(r"^(FLIGHT|FUEL|WEIGHT|NOTAM|END)\b", u):
                    break
                if len(ln.strip()) > 8 and re.search(r"[A-Z]{3,5}", u):
                    between.append(ln.strip())
                elif between:
                    break
        if between:
            route = " ".join(between)
    out["route"] = (route or "").strip()

    return out
