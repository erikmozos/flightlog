"""
Parser tolerante para el XML Datafile de SimBrief (stdlib únicamente).
Probamos variaciones habituales de etiquetas porque el XSD no viene documentado aquí de forma estable.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

_LB_TO_KG = Decimal("0.45359237")

# Umbrales: SimBrief suele usar epoch Unix (>1e9) en <times>; ETE/AET en segundos.
_UNIX_TS_MIN_ABS = int(9.5 * 10**8)  # ~ 2001-01 ; evita confusiones con otros enteros grandes
_SECONDS_ENROUTE_MAX = 86400 * 3  # hasta ~72 h de ETE antes de usar otro heuristic

# Subnodos donde suele estar el ICAO aeródromo dentro de cada bloque lógico.
_ICAO_AIRPORT_TAGS = frozenset({"icao_code", "icao", "code_airport"})

_ORIGIN_TAGS = frozenset({"origin", "departure", "from_airport", "origin_airport"})
_DEST_TAGS = frozenset({"destination", "arrival", "to_airport", "destination_airport", "dest"})
_ALT_TAGS = frozenset({"alternate", "alternates", "alternate_airport", "altn"})
_AIRCRAFT_BLOCK_TAGS = frozenset({"aircraft", "aircraft_details", "airplane", "equipment"})
_AIRCRAFT_TYPE_TAGS = frozenset(
    {
        "icaocode",
        "icao_code",
        "icao",
        "type",
        "equipment_code",
        "equipment",
        "aircraft_code",
    }
)


def _local_tag(tag: str) -> str:
    if not tag:
        return ""
    return tag.rsplit("}", 1)[-1].strip().lower()


def _norm_str(s: str | None) -> str:
    return (s or "").strip()


def _decimal_or_none(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    s = _norm_str(raw).replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _fuel_mass_to_kg(value: Decimal | None, unit_hint: str) -> Decimal | None:
    if value is None:
        return None
    u = (unit_hint or "").lower()
    if "lb" in u:
        out = value * _LB_TO_KG
    else:
        out = value
    return out.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _params_fuel_unit(root: ET.Element) -> str:
    params = _first_matching_block(root, frozenset({"params"}))
    if params is None:
        return "kgs"
    for child in params:
        if _local_tag(child.tag) == "units":
            t = _norm_str(child.text)
            return t.lower() if t else "kgs"
    return "kgs"


def _parse_fuel_kg(root: ET.Element) -> dict[str, Any]:
    unit = _params_fuel_unit(root)
    fuel_el = _first_matching_block(root, frozenset({"fuel"}))
    out: dict[str, Any] = {
        "ofp_fuel_ramp_kg": None,
        "ofp_fuel_takeoff_kg": None,
        "ofp_fuel_landing_kg": None,
    }
    if fuel_el is None:
        return out
    mapping = {
        "plan_ramp": "ofp_fuel_ramp_kg",
        "plan_takeoff": "ofp_fuel_takeoff_kg",
        "plan_landing": "ofp_fuel_landing_kg",
    }
    for el in fuel_el.iter():
        lc = _local_tag(el.tag)
        if lc not in mapping:
            continue
        val = _decimal_or_none(_text_or_none(el))
        if val is not None:
            out[mapping[lc]] = _fuel_mass_to_kg(val, unit)
    return out


def _norm_airport_icao(raw: str | None) -> str | None:
    t = (raw or "").strip().upper()
    if len(t) == 4 and t.isalpha():
        return t
    return None


def _text_or_none(el: ET.Element | None) -> str | None:
    if el is None:
        return None
    txt = _norm_str(el.text)
    return txt if txt else None


def _extract_airport_under(container: ET.Element) -> str | None:
    """ICAO dentro de un bloque <origin>, <destination>, etc.; ignora texto no válido."""
    for sub in container.iter():
        if sub is container and sub.text:
            t = _norm_airport_icao(sub.text)
            if t:
                return t
        lc = _local_tag(sub.tag)
        if lc in _ICAO_AIRPORT_TAGS:
            t = _norm_airport_icao(_norm_str(sub.text))
            if t:
                return t
        # algunos dumps usan <ident>XXXX</ident>
        if lc in ("ident", "ident_code", "id"):
            t = _norm_airport_icao(_norm_str(sub.text))
            if t:
                return t
    return None


def _first_matching_block(root: ET.Element, names: frozenset[str]) -> ET.Element | None:
    """Primer elemento cuyo tag local coincide (depth-first estándar de iter())."""
    for el in root.iter():
        if _local_tag(el.tag) in names:
            return el
    return None


def _gather_general_fields(root: ET.Element) -> dict[str, str]:
    gen = _first_matching_block(root, frozenset({"general", "trip", "dispatch"}))
    out: dict[str, str] = {}
    if gen is None:
        return out
    for child in gen:
        k = _local_tag(child.tag)
        v = _text_or_none(child)
        if v:
            out[k] = v
    return out


def _icao_from_sections(root: ET.Element, tagset: frozenset[str]) -> str | None:
    block = _first_matching_block(root, tagset)
    if block is not None:
        icao = _extract_airport_under(block)
        if icao:
            return icao
    return None


def _alternate_icao(root: ET.Element) -> str | None:
    candidates: list[tuple[int, ET.Element]] = []
    for el in root.iter():
        lc = _local_tag(el.tag)
        if lc in _ALT_TAGS or lc.startswith("alternate"):
            prio = int(el.attrib.get("idx", el.attrib.get("index", "99")))
            candidates.append((prio, el))
    candidates.sort(key=lambda x: x[0])
    for _, el in candidates:
        icao = _extract_airport_under(el)
        if icao:
            return icao
    # A veces <alternates><alternate>...</alternate>
    alt_block = _first_matching_block(root, frozenset({"alternates"}))
    if alt_block is not None:
        for sub in alt_block:
            if _local_tag(sub.tag) in frozenset({"alternate", "airport"}):
                icao = _extract_airport_under(sub)
                if icao:
                    return icao
    return None


def _aircraft_icao(root: ET.Element) -> str | None:
    """
    Tipo OACI (B738, A320…) en el bloque <aircraft> o elemento suelto <icaocode> (Sin escanear
    <icao_code> global de aeródromos).
    """
    block = _first_matching_block(root, _AIRCRAFT_BLOCK_TAGS)
    if block is not None:
        for el in block.iter():
            lc = _local_tag(el.tag)
            if lc not in _AIRCRAFT_TYPE_TAGS:
                continue
            txt = _norm_str(el.text)
            if not txt:
                continue
            cand = "".join(c for c in txt.upper() if c.isalnum())[:16]
            if cand and cand[0].isalpha():
                return cand

    for el in root.iter():
        if _local_tag(el.tag) == "icaocode":
            txt = _norm_str(el.text)
            if not txt:
                continue
            cand = "".join(c for c in txt.upper() if c.isalnum())[:16]
            if cand and cand[0].isalpha():
                return cand
    return None


def _departure_clock_from_text(txt: str | None) -> time | None:
    """
    Horas locales programadas desde SimBrief: a menudo <sched_out> es epoch Unix en segundos;
    otros campos pueden ser HH:MM / HHMM o fragmentos más largos con fecha.
    """
    if txt is None:
        return None
    s = _norm_str(txt)
    if not s:
        return None
    if s.isdigit() and len(s) >= 9:
        try:
            ts = int(s)
            if ts < _UNIX_TS_MIN_ABS:
                return None
            return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None).time()
        except (ValueError, OSError, OverflowError):
            return None
    if ("T" in s and ":" in s) or re.match(r"^\d{4}-\d{2}-\d{2}", s):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt.time()
        except ValueError:
            pass
    return _parse_time_fragment(s)


def _parse_time_fragment(s: str) -> time | None:
    s = _norm_str(s).upper().replace("Z", "")
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})(?:\s*:\s*(\d{2}))?", s)
    if m:
        try:
            h, mi = int(m.group(1)), int(m.group(2))
            sec = int(m.group(3)) if m.group(3) else 0
        except ValueError:
            return None
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return time(h, mi, sec)
    m2 = re.search(r"\b(\d{3,4})\b", s)
    if m2:
        raw = m2.group(1)
        if len(raw) == 4:
            try:
                h, mi = int(raw[:2]), int(raw[2:])
            except ValueError:
                return None
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return time(h, mi, 0)
    return None


def _planned_departure(root: ET.Element, general: dict[str, str]) -> time | None:
    time_tags = frozenset(
        {
            "sched_out",
            "sched_deptime",
            "scheduled_deptime",
            "deptime",
            "dep_time",
            "std",
            "est_off",
            "estimated_off_block",
            "etd",
            "time_out",
            "utc_out",
            "planned_deptime",
        }
    )
    times_block = _first_matching_block(root, frozenset({"times"}))
    if times_block is not None:
        for el in times_block.iter():
            if _local_tag(el.tag) in time_tags:
                txt = _text_or_none(el)
                if txt:
                    tp = _departure_clock_from_text(txt)
                    if tp:
                        return tp
    for gen_key in ("scheduled_deptime", "deptime", "std"):
        if gen_key in general:
            t = _departure_clock_from_text(general[gen_key])
            if t:
                return t

    origin = _first_matching_block(root, _ORIGIN_TAGS)
    search_order: list[ET.Element | None] = [origin]
    search_order.append(root)
    for sr in search_order:
        if sr is None:
            continue
        for el in sr.iter():
            if _local_tag(el.tag) in time_tags:
                txt = _text_or_none(el)
                if txt:
                    tp = _departure_clock_from_text(txt)
                    if tp:
                        return tp
    return None


def _enroute_timedelta_seconds_only(raw: str | None) -> timedelta | None:
    """Campo típico de SimBrief: entero como segundos (p. ej. est_time_enroute 2320)."""
    if raw is None:
        return None
    s = _norm_str(raw)
    if not s.isdigit():
        return None
    try:
        sec = int(s)
    except ValueError:
        return None
    if sec <= 0 or sec > _SECONDS_ENROUTE_MAX:
        return None
    return timedelta(seconds=sec)


def _estimated_enroute(general: dict[str, str], root: ET.Element) -> timedelta | None:
    raw_keys = (
        "est_time_enroute",
        "scheduled_time_enroute",
        "time_enroute",
        "route_time",
        "ete",
        "eet",
    )
    for k in raw_keys:
        if k in general:
            td = _enroute_timedelta_seconds_only(general[k]) or _parse_duration_string(
                general[k]
            )
            if td:
                return td

    dur_tags = frozenset(raw_keys) | frozenset({"estimated_time_enroute", "flt_time"})
    for el in root.iter():
        if _local_tag(el.tag) in dur_tags:
            raw = _text_or_none(el)
            td = _enroute_timedelta_seconds_only(raw) or _parse_duration_string(raw)
            if td:
                return td
    return None


def _parse_duration_string(raw: str | None) -> timedelta | None:
    if raw is None:
        return None
    s = _norm_str(raw)
    # "1h25", "01:35", "0135"
    m = re.search(r"(\d+)\s*H\s*(\d+)", s, re.I)
    if m:
        try:
            return timedelta(hours=int(m.group(1)), minutes=int(m.group(2)))
        except ValueError:
            return None
    m = re.search(r"(?<!:)(\d+)\s*:\s*(\d+)(?:\s*:\s*(\d+))?", s)
    if m:
        try:
            h = int(m.group(1))
            mi = int(m.group(2))
            sec = int(m.group(3)) if m.group(3) else 0
        except ValueError:
            return None
        if h < 48:
            return timedelta(hours=h, minutes=mi, seconds=sec)
    m2 = re.search(r"\b(\d{3,4})\b", s)
    if m2 and ":" not in s:
        rawd = m2.group(1)
        if len(rawd) == 4:
            try:
                h, mi = int(rawd[:2]), int(rawd[2:])
            except ValueError:
                return None
            if h < 48 and mi < 60:
                return timedelta(hours=h, minutes=mi)
    return None


def _route_string(root: ET.Element) -> str:
    gen = _first_matching_block(root, frozenset({"general", "trip", "dispatch"}))
    if gen is not None:
        for pref in ("route", "route_navigraph", "route_ifps"):
            for child in gen:
                if _local_tag(child.tag) == pref:
                    txt = _norm_str(child.text)
                    if txt:
                        return txt

    atc = _first_matching_block(root, frozenset({"atc"}))
    if atc is not None:
        for child in atc:
            if _local_tag(child.tag) == "route":
                txt = _norm_str(child.text)
                if txt:
                    return txt

    bad_route_ancestors = _ALT_TAGS | frozenset(
        {"alternate_navlog", "takeoff_altn", "enroute_altn"}
    )

    parent: dict[ET.Element, ET.Element] = {}
    for p in root.iter():
        for c in p:
            parent[c] = p

    def under_bad(el: ET.Element) -> bool:
        cur: ET.Element | None = el
        while cur is not None:
            if _local_tag(cur.tag) in bad_route_ancestors:
                return True
            cur = parent.get(cur)
        return False

    best = ""
    for el in root.iter():
        lc = _local_tag(el.tag)
        if lc not in ("route", "planned_route", "route_text", "airway_route"):
            continue
        if under_bad(el):
            continue
        txt = _norm_str(el.text)
        if txt and len(txt) > len(best):
            best = txt
    if best:
        return best

    # Navlog: ident / name / waypoint
    nav = _first_matching_block(root, frozenset({"navlog", "nav_log", "waypoints"}))
    if nav is None:
        return ""
    ids: list[str] = []
    for pt in nav.iter():
        if _local_tag(pt.tag) not in frozenset({"fix", "waypoint", "point", "wpt"}):
            continue
        ident = None
        for ch in pt:
            lcc = _local_tag(ch.tag)
            if lcc in ("ident", "name", "id", "waypoint_id"):
                ident = _norm_str(ch.text)
                if ident:
                    break
        if not ident and pt.text:
            ident = _norm_str(pt.text)
        if ident:
            ids.append(ident)
    return " ".join(ids) if ids else ""


def _strip_xml_blocks_by_local_name(raw: str, *local_names: str) -> str:
    """
    Elimina el interior de nodos grandes (p. ej. <text>…</text>) que a menudo
    contienen HTML con «&» sin escapar y hacen fallar ET.fromstring.
    Sustituye cada bloque por una etiqueta vacía conservando el nombre local.
    """
    s = raw
    for name in local_names:
        if not name:
            continue
        pat = re.compile(
            rf"<{re.escape(name)}\b[^>]*>.*?</{re.escape(name)}>",
            re.DOTALL | re.IGNORECASE,
        )
        s = pat.sub(f"<{name}/>", s)
    return s


def _escape_bare_ampersands_for_xml(s: str) -> str:
    """
    Convierte «&» que no abren una entidad XML válida en &amp;
    (útil si queda contenido mal formado tras saneamientos).
    """
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != "&":
            out.append(s[i])
            i += 1
            continue
        m = re.match(
            r"&(#[0-9]{1,7}|#x[0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]{0,47});",
            s[i:],
        )
        if m:
            out.append(m.group(0))
            i += len(m.group(0))
        else:
            out.append("&amp;")
            i += 1
    return "".join(out)


def _regex_first_icao_in_block(raw: str, block_tag: str) -> str | None:
    """Primer ICAO de aeródromo (4 letras) en <block_tag>…</block_tag>."""
    m = re.search(
        rf"<{re.escape(block_tag)}\b[^>]*>(?P<inner>.*?)</{re.escape(block_tag)}>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    inner = m.group("inner")
    m2 = re.search(
        r"<(?:icao_code|icao)\b[^>]*>\s*([A-Za-z]{4})\s*</",
        inner,
        re.IGNORECASE,
    )
    if not m2:
        return None
    return _norm_airport_icao(m2.group(1))


def _regex_aircraft_icao(raw: str) -> str | None:
    """Tipo OACI dentro de <aircraft>…</aircraft> (icaocode / icao_code)."""
    m = re.search(
        r"<aircraft\b[^>]*>(?P<inner>.*?)</aircraft>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    inner = m.group("inner")
    for pat in (
        r"<(?:icaocode|icao_code)\b[^>]*>\s*([A-Za-z0-9]{2,16})\s*</",
        r"<type\b[^>]*>\s*([A-Za-z0-9]{2,16})\s*</",
    ):
        m2 = re.search(pat, inner, re.IGNORECASE)
        if not m2:
            continue
        cand = "".join(c for c in m2.group(1).upper() if c.isalnum())[:16]
        if cand and cand[0].isalpha():
            return cand
    return None


def _regex_alternate_icao(raw: str) -> str | None:
    m = re.search(
        r"<alternate\b[^>]*>(?P<inner>.*?)</alternate>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    inner = m.group("inner")
    m2 = re.search(
        r"<(?:icao_code|icao)\b[^>]*>\s*([A-Za-z]{4})\s*</",
        inner,
        re.IGNORECASE,
    )
    if not m2:
        return None
    return _norm_airport_icao(m2.group(1))


def _regex_route_string(raw: str) -> str:
    m = re.search(
        r"<general\b[^>]*>(?P<inner>.*?)</general>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        inner = m.group("inner")
        for child in ("route", "route_navigraph", "route_ifps"):
            m2 = re.search(
                rf"<{re.escape(child)}\b[^>]*>([^<]*)</{re.escape(child)}>",
                inner,
                re.IGNORECASE,
            )
            if m2:
                t = _norm_str(m2.group(1))
                if t:
                    return t
    m_atc = re.search(
        r"<atc\b[^>]*>(?P<inner>.*?)</atc>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if m_atc:
        m3 = re.search(
            r"<route\b[^>]*>([^<]*)</route>",
            m_atc.group("inner"),
            re.IGNORECASE | re.DOTALL,
        )
        if m3:
            t = _norm_str(m3.group(1))
            if t:
                return t
    return ""


def _regex_params_units(raw: str) -> str:
    m = re.search(r"<units\b[^>]*>\s*([^<]+?)\s*</units>", raw, re.I | re.DOTALL)
    if not m:
        return "kgs"
    return (m.group(1) or "").strip().lower()


def _regex_sched_out_time(raw: str) -> time | None:
    m = re.search(
        r"<sched_out\b[^>]*>\s*([\d]{8,})\s*</sched_out>",
        raw,
        re.I,
    )
    if not m:
        return None
    return _departure_clock_from_text(m.group(1))


def _regex_fuel_kg_dict(raw: str) -> dict[str, Any]:
    unit = _regex_params_units(raw)
    out: dict[str, Any] = {
        "ofp_fuel_ramp_kg": None,
        "ofp_fuel_takeoff_kg": None,
        "ofp_fuel_landing_kg": None,
    }
    m = re.search(r"<fuel\b[^>]*>(?P<inner>.*?)</fuel>", raw, re.DOTALL | re.I)
    if not m:
        return out
    inner = m.group("inner")

    def grab(tag: str) -> Decimal | None:
        m2 = re.search(
            rf"<{re.escape(tag)}\b[^>]*>\s*([\d.,]+)\s*</{re.escape(tag)}>",
            inner,
            re.I | re.DOTALL,
        )
        if not m2:
            return None
        return _decimal_or_none(m2.group(1))

    out["ofp_fuel_ramp_kg"] = _fuel_mass_to_kg(grab("plan_ramp"), unit)
    out["ofp_fuel_takeoff_kg"] = _fuel_mass_to_kg(grab("plan_takeoff"), unit)
    out["ofp_fuel_landing_kg"] = _fuel_mass_to_kg(grab("plan_landing"), unit)
    return out


def _regex_est_time_enroute(raw: str) -> timedelta | None:
    m = re.search(r"<general\b[^>]*>(?P<inner>.*?)</general>", raw, re.DOTALL | re.I)
    if not m:
        return None
    inner = m.group("inner")
    m2 = re.search(
        r"<est_time_enroute\b[^>]*>\s*([\d]+)\s*</est_time_enroute>",
        inner,
        re.I,
    )
    if not m2:
        return None
    return _enroute_timedelta_seconds_only(m2.group(1))


def _regex_flight_number(raw: str) -> str | None:
    m = re.search(
        r"<general\b[^>]*>(?P<inner>.*?)</general>",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    inner = m.group("inner")
    m2 = re.search(
        r"<flight_number\b[^>]*>([^<]*)</flight_number>",
        inner,
        re.IGNORECASE,
    )
    if m2:
        fn = _norm_str(m2.group(1))
        return fn[:20] if fn else None
    return None


def _flight_number(root: ET.Element, general: dict[str, str]) -> str | None:
    fn = general.get("flight_number") or general.get("fltno") or general.get("flight_no")
    if fn:
        return fn[:20]
    al = _norm_str(general.get("icao_airline") or general.get("airline") or "")
    num = _norm_str(general.get("flight_number_num") or general.get("number") or "")
    if al and num:
        return f"{al}{num}"[:20]

    for el in root.iter():
        if _local_tag(el.tag) in frozenset(
            {"flight_number", "callsign", "fltno", "flightnumber"}
        ):
            txt = _text_or_none(el)
            if txt:
                return txt[:20]
    return None


def _parse_tree_to_dict(root: ET.Element) -> dict[str, Any]:
    general = _gather_general_fields(root)
    dep = _icao_from_sections(root, _ORIGIN_TAGS)
    arr = _icao_from_sections(root, _DEST_TAGS)
    if not dep or not arr:
        found: list[str] = []
        for el in root.iter():
            if _local_tag(el.tag) not in _ICAO_AIRPORT_TAGS:
                continue
            c = _norm_airport_icao(_text_or_none(el))
            if c and c not in found:
                found.append(c)
            if len(found) >= 2:
                break
        if not dep and found:
            dep = found[0]
        if not arr and len(found) >= 2:
            arr = found[1]

    fuel = _parse_fuel_kg(root)
    return {
        "flight_number": _flight_number(root, general),
        "departure_icao": dep,
        "arrival_icao": arr,
        "alternate_icao": _alternate_icao(root),
        "aircraft_icao": _aircraft_icao(root),
        "route": _route_string(root) or "",
        "planned_departure_time": _planned_departure(root, general),
        "estimated_flight_time": _estimated_enroute(general, root),
        **fuel,
    }


def _regex_snapshot(raw: str) -> dict[str, Any]:
    """Extracción tolerante cuando ElementTree falla o deja campos vacíos."""
    fuel = _regex_fuel_kg_dict(raw)
    ete = _regex_est_time_enroute(raw)
    sched = _regex_sched_out_time(raw)
    base = {
        "flight_number": _regex_flight_number(raw),
        "departure_icao": _regex_first_icao_in_block(raw, "origin"),
        "arrival_icao": _regex_first_icao_in_block(raw, "destination"),
        "alternate_icao": _regex_alternate_icao(raw),
        "aircraft_icao": _regex_aircraft_icao(raw),
        "route": _regex_route_string(raw),
        "planned_departure_time": sched,
        "estimated_flight_time": ete,
        **fuel,
    }
    return base


def _merge_simbrief_dict(
    primary: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    out = dict(primary)
    str_keys = (
        "flight_number",
        "departure_icao",
        "arrival_icao",
        "alternate_icao",
        "aircraft_icao",
    )
    for k in str_keys:
        if not (out.get(k) or "").strip():
            v = fallback.get(k)
            if v:
                out[k] = v
    if not (out.get("route") or "").strip():
        r = fallback.get("route")
        if r:
            out["route"] = r
    if out.get("planned_departure_time") is None:
        out["planned_departure_time"] = fallback.get("planned_departure_time")
    if out.get("estimated_flight_time") is None:
        out["estimated_flight_time"] = fallback.get("estimated_flight_time")
    for fk in (
        "ofp_fuel_ramp_kg",
        "ofp_fuel_takeoff_kg",
        "ofp_fuel_landing_kg",
    ):
        if out.get(fk) is None and fallback.get(fk) is not None:
            out[fk] = fallback[fk]
    return out


def _tree_dict_quality(d: dict[str, Any]) -> int:
    """Ponderación simple para elegir el mejor árbol parseado."""
    n = 0
    if d.get("departure_icao"):
        n += 4
    if d.get("arrival_icao"):
        n += 4
    if d.get("aircraft_icao"):
        n += 3
    if (d.get("route") or "").strip():
        n += 2
    if d.get("flight_number"):
        n += 1
    if d.get("estimated_flight_time") is not None:
        n += 1
    if d.get("planned_departure_time") is not None:
        n += 1
    for fk in ("ofp_fuel_ramp_kg", "ofp_fuel_takeoff_kg", "ofp_fuel_landing_kg"):
        if d.get(fk) is not None:
            n += 1
    return n


def _xml_parse_roots(raw: str) -> list[ET.Element]:
    """
    Intentos de parseo: el nodo <text> suele incluir HTML con '&' ilegales;
    al recortarlo o escapar '&' suelen obtenerse árboles válidos.
    """
    stripped = _strip_xml_blocks_by_local_name(raw, "text")
    variants: list[str] = []
    for v in (
        stripped,
        _escape_bare_ampersands_for_xml(stripped),
        raw,
        _escape_bare_ampersands_for_xml(raw),
    ):
        if v and v not in variants:
            variants.append(v)

    roots: list[ET.Element] = []
    for v in variants:
        try:
            roots.append(ET.fromstring(v))
        except ET.ParseError:
            continue
    return roots


def parse_simbrief_xml(xml_content: str) -> dict[str, Any]:
    """
    Extrae campos del XML Datafile de SimBrief. Estructura variable: nunca lanza; devuelve vacíos.
    El XML completo de SimBrief a menudo no es XML 100 % bien formado (HTML en <text>);
    se recorta <text>, se reintenta y, si hace falta, se usan expresiones regulares.
    """
    empty: dict[str, Any] = {
        "flight_number": None,
        "departure_icao": None,
        "arrival_icao": None,
        "alternate_icao": None,
        "aircraft_icao": None,
        "route": "",
        "planned_departure_time": None,
        "estimated_flight_time": None,
        "ofp_fuel_ramp_kg": None,
        "ofp_fuel_takeoff_kg": None,
        "ofp_fuel_landing_kg": None,
    }
    if xml_content is None:
        return empty
    raw = xml_content.strip() if isinstance(xml_content, str) else ""
    if not raw:
        return empty

    fb = _regex_snapshot(raw)

    roots = _xml_parse_roots(raw)
    if not roots:
        return _merge_simbrief_dict(empty, fb)

    best: dict[str, Any] | None = None
    best_q = -1
    for root in roots:
        try:
            candidate = _parse_tree_to_dict(root)
        except Exception:
            continue
        q = _tree_dict_quality(candidate)
        if q > best_q:
            best_q = q
            best = candidate

    if best is None:
        return _merge_simbrief_dict(empty, fb)

    return _merge_simbrief_dict(best, fb)
