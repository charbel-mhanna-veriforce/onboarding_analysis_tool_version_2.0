"""
ULTRA-FAST Backend - with detailed timing logs + legacy CBX logic
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
import uuid
import shutil
from pathlib import Path
import logging
from rapidfuzz import fuzz
import re
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import string

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

jobs: Dict[str, Dict[str, Any]] = {}


def update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)

# -------------------------------------------------------------------
# CONSTANTS & HELPERS (ported/adapted from legacy script)
# -------------------------------------------------------------------

# Legacy analysis headers (same as old script)
# Legacy analysis headers (exact order from old script / sample Excel)
ANALYSIS_HEADERS = [
    "cbx_id",
    "hc_contractor_summary",
    "analysis",
    "cbx_contractor",
    "cbx_street",
    "cbx_city",
    "cbx_state",
    "cbx_zip",
    "cbx_country",
    "cbx_expiration_date",
    "registration_status",
    "suspended",
    "cbx_email",
    "cbx_first_name",
    "cbx_last_name",
    "modules",
    "cbx_account_type",
    "cbx_subscription_fee",
    "cbx_employee_price",
    "parents",
    "previous",
    "hiring_client_names",
    "hiring_client_count",
    "is_in_relationship",
    "is_qualified",
    "ratio_company",
    "ratio_address",
    "contact_match",
    "cbx_assessment_level",
    "new_product",
    "generic_domain",
    "match_count",
    "match_count_with_hc",
    "is_subscription_upgrade",
    "upgrade_price",
    "prorated_upgrade_price",
    "create_in_cbx",
    "action",
    "index",
]


# How our internal column names map to the legacy analysis headers
INTERNAL_ANALYSIS_MAP = {
    "cbx_id": "cbx_id",
    "hc_contractor_summary": "hc_contractor_summary",
    "analysis": "analysis",
    "cbx_contractor": "company",              # old 'company'
    "cbx_street": "address",
    "cbx_city": "city",
    "cbx_state": "state",
    "cbx_zip": "zip",
    "cbx_country": "country",
    "cbx_expiration_date": "expiration_date",
    "registration_status": "registration_status",
    "suspended": "suspended",
    "cbx_email": "email",
    "cbx_first_name": "first_name",
    "cbx_last_name": "last_name",
    "modules": "modules",
    "cbx_account_type": "account_type",
    "cbx_subscription_fee": "subscription_price",
    "cbx_employee_price": "employee_price",
    "parents": "parents",
    "previous": "previous",
    "hiring_client_names": "hiring_client_names",
    "hiring_client_count": "hiring_client_count",
    "is_in_relationship": "is_in_relationship",
    "is_qualified": "is_qualified",
    "ratio_company": "ratio_company",
    "ratio_address": "ratio_address",
    "contact_match": "contact_match",
    "cbx_assessment_level": "cbx_assessment_level",
    "new_product": "new_product",
    "generic_domain": "generic_domain",
    "match_count": "match_count",
    "match_count_with_hc": "match_count_with_hc",
    "is_subscription_upgrade": "subscription_upgrade",
    "upgrade_price": "upgrade_price",
    "prorated_upgrade_price": "prorated_upgrade_price",
    "create_in_cbx": "create_in_cbx",
    "action": "action",
    "index": "row_index",   # internal name we use
}

# EXACT copy of BASE_GENERIC_DOMAIN from legacy script
GENERIC_DOMAINS_LIST = [
    "yahoo.ca", "yahoo.com", "hotmail.com", "gmail.com", "outlook.com",
    "bell.com", "bell.ca", "videotron.ca", "eastlink.ca", "kos.net", "bellnet.ca", "sasktel.net",
    "aol.com", "tlb.sympatico.ca", "sogetel.net", "cgocable.ca",
    "hotmail.ca", "live.ca", "icloud.com", "hotmail.fr", "yahoo.com", "outlook.fr", "msn.com",
    "globetrotter.net", "live.com", "sympatico.ca", "live.fr", "yahoo.fr", "telus.net",
    "shaw.ca", "me.com", "bell.net", "cablevision.qc.ca", "live.ca", "tlb.sympatico.ca",
    "", "videotron.qc.ca", "ivic.qc.ca", "qc.aira.com", "canada.ca", "axion.ca", "bellsouth.net",
    "telusplanet.net", "rogers.com", "mymts.net", "nb.aibn.com", "on.aibn.com", "live.be",
    "nbnet.nb.ca",
    "execulink.com", "bellaliant.com", "nf.aibn.com", "clintar.com", "pathcom.com", "oricom.ca",
    "mts.net",
    "xplornet.com", "mcsnet.ca", "att.net", "ymail.com", "mail.com", "bellaliant.net",
    "ns.sympatico.ca",
    "ns.aliantzinc.ca", "mnsi.net"
]

# Use a set for fast membership while preserving the exact values from legacy
GENERIC_DOMAINS = set(GENERIC_DOMAINS_LIST)


GENERIC_COMPANY_NAME_WORDS = [
    "construction", "contracting", "industriel", "industriels", "service",
    "services", "inc", "limited", "ltd", "ltee", "ltée", "co", "industrial",
    "solutions", "llc", "enterprises", "systems", "industries",
    "technologies", "company", "corporation", "installations", "enr",
]

SUPPORTED_CURRENCIES = ("CAD", "USD")

CBX_DEFAULT_STANDARD_SUBSCRIPTION = 803  # same as legacy

assessment_levels = {
    "gold": 2,
    "silver": 2,
    "bronze": 1,
    "level3": 2,
    "level2": 2,
    "level1": 1,
    "3": 2,
    "2": 2,
    "1": 1,
}

LIST_SEPARATOR = ";"  # used in hiring_client_names, etc.


def smart_boolean(val: Any) -> bool:
    """Try to interpret many string booleans into True/False."""
    if isinstance(val, str):
        v = val.strip().lower()
        return v in ("true", "=true", "yes", "vraie", "=vraie", "1", "y", "oui")
    return bool(val)


def norm_name(name: Any) -> str:
    if not name:
        return ""
    # Remove punctuation, lowercase, strip whitespace
    return (
        str(name)
        .translate(str.maketrans("", "", string.punctuation))
        .strip()
        .lower()
    )


def parse_assessment_level(level: Any) -> int:
    if level is None:
        return 0
    if isinstance(level, int):
        if 0 < level < 4:
            return level
        return 0
    if isinstance(level, str):
        key = level.lower().strip()
        return assessment_levels.get(key, 0)
    return 0


def core_mandatory_provided(hc: Dict[str, Any]) -> bool:
    """
    Mandatory fields:
    company, first name, last name, email, contact_phone,
    address, city, state (if CA/US), country, zip.
    """
    mandatory_fields = (
        "contractor_name",
        "contact_first_name",
        "contact_last_name",
        "contact_email",
        "contact_phone",
        "address",
        "city",
        "province_state_iso2",
        "country_iso2",
        "postal_code",
    )
    country = (hc.get("country_iso2") or "").strip().lower()
    for field in mandatory_fields:
        value = hc.get(field)
        if isinstance(value, str):
            value = value.strip()
        if not value:
            if field == "province_state_iso2" and country not in ("ca", "us"):
                # State can be empty if not CA/US
                continue
            return False
    return True


def action_for_row(
    hc: Dict[str, Any],
    cbx_match: Dict[str, Any],
    create_in_cbx: bool,
    subscription_update: bool,
    expiration_date: Optional[datetime],
    is_qualified: bool,
) -> str:
    """
    Port of legacy `action()` logic, adapted for dict-based rows.
    """
    reg_status = (cbx_match.get("registration_status") or "").strip()
    is_take_over = smart_boolean(hc.get("is_take_over"))
    is_association_fee = smart_boolean(hc.get("is_association_fee"))

    if create_in_cbx:
        # CREATE path
        if is_take_over:
            return "activation_link"
        else:
            ambiguous = smart_boolean(hc.get("ambiguous"))
            if ambiguous:
                return "ambiguous_onboarding"
            elif core_mandatory_provided(hc):
                return "onboarding"
            else:
                return "missing_info"
    else:
        # UPDATE path
        if is_take_over:
            if reg_status == "Suspended":
                return "restore_suspended"
            elif reg_status == "Active":
                return "add_questionnaire"
            elif reg_status == "Non Member":
                return "activation_link"
            else:
                # Unknown reg_status: be safe
                return "add_questionnaire"

        # Not takeover
        if reg_status == "Active":
            if cbx_match.get("is_in_relationship"):
                qstatus = cbx_match.get("matched_qstatus")
                if qstatus == "validated":
                    return "already_qualified"
                elif qstatus in ("pending", "expired", "conditional", "refused"):
                    return "follow_up_qualification"
                else:
                    # Unknown/missing qstatus – fallback to is_qualified flag
                    return "already_qualified" if is_qualified else "follow_up_qualification"
            else:
                # Not in relationship
                if subscription_update:
                    return "subscription_upgrade"
                elif is_association_fee and not cbx_match.get("is_in_relationship"):
                    if expiration_date:
                        in_60_days = datetime.now() + timedelta(days=60)
                        if expiration_date > in_60_days:
                            return "association_fee"
                        else:
                            return "add_questionnaire"
                    else:
                        return "association_fee"
                else:
                    return "add_questionnaire"

        elif reg_status == "Suspended":
            return "restore_suspended"
        elif reg_status in ("Non Member", "", None):
            return "re_onboarding"
        else:
            # Strange status, keep safe
            return "unknown"


def to_float(val: Any) -> float:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return 0.0
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def add_analysis_data(
    hc: Dict[str, Any],
    cbx_row: pd.Series,
    ratio_company: Optional[float] = None,
    ratio_address: Optional[float] = None,
    contact_match: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Build the analysis dict for a single CBX match (port of legacy add_analysis_data).
    """
    cbx_company = cbx_row.get("name_fr") or cbx_row.get("name_en")

    # Hiring client relationship info
    names_str = cbx_row.get("hiring_client_names") or ""
    hiring_clients_list = [
        norm_name(x) for x in str(names_str).split(LIST_SEPARATOR) if x
    ]
    qstatus_str = cbx_row.get("hiring_client_qstatus") or ""
    hiring_clients_qstatus = [
        (s or "").strip().lower()
        for s in str(qstatus_str).split(LIST_SEPARATOR)
        if s
    ]

    hc_name_norm = norm_name(hc.get("hiring_client_name"))
    hc_count = len(hiring_clients_list) if names_str else 0
    is_in_relationship = hc_name_norm in hiring_clients_list and hc_name_norm != ""
    is_qualified = False
    matched_qstatus = None

    for idx, val in enumerate(hiring_clients_list):
        if val == hc_name_norm and idx < len(hiring_clients_qstatus):
            qstatus = hiring_clients_qstatus[idx]
            matched_qstatus = qstatus
            if qstatus == "validated":
                is_qualified = True
            break

    # Prices
    sub_price_usd = to_float(cbx_row.get("subscription_price_usd"))
    employee_price_usd = to_float(cbx_row.get("employee_price_usd"))
    sub_price_cad = to_float(cbx_row.get("subscription_price_cad"))
    employee_price_cad = to_float(cbx_row.get("employee_price_cad"))

    contact_currency = (hc.get("contact_currency") or "").upper()
    if contact_currency and contact_currency not in SUPPORTED_CURRENCIES:
        logger.warning(
            f"Invalid currency: {contact_currency} for contractor {hc.get('contractor_name')}, "
            f"expected one of {SUPPORTED_CURRENCIES}"
        )

    subscription_price = sub_price_cad if contact_currency == "CAD" else sub_price_usd
    employee_price = (
        employee_price_cad if contact_currency == "CAD" else employee_price_usd
    )

    # Expiration date parsing
    expiration_date = None
    exp_raw = cbx_row.get("cbx_expiration_date")
    if isinstance(exp_raw, datetime):
        expiration_date = exp_raw
    elif isinstance(exp_raw, str) and exp_raw.strip():
        for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                expiration_date = datetime.strptime(exp_raw.strip(), fmt)
                break
            except ValueError:
                continue

    # Summary for analysis column
    hiring_client_contractor_summary = (
        f"{hc.get('contractor_name', '')}, {hc.get('address', '')}, {hc.get('city', '')}, "
        f"{hc.get('province_state_iso2', '')}, {hc.get('country_iso2', '')}, "
        f"{hc.get('postal_code', '')}, {hc.get('contact_email', '')}, "
        f"{hc.get('contact_first_name', '')} {hc.get('contact_last_name', '')}"
    )

    return {
        "cbx_id": cbx_row.get("id"),
        "hc_contractor_summary": hiring_client_contractor_summary,
        "analysis": "",
        "company": cbx_company,
        "address": cbx_row.get("address"),
        "city": cbx_row.get("city"),
        "state": cbx_row.get("state"),
        "zip": cbx_row.get("postal_code"),
        "country": cbx_row.get("country"),
        "expiration_date": expiration_date,
        "registration_status": cbx_row.get("registration_code"),
        "suspended": cbx_row.get("suspended"),
        "email": cbx_row.get("email"),
        "first_name": cbx_row.get("first_name"),
        "last_name": cbx_row.get("last_name"),
        "modules": cbx_row.get("modules"),
        "account_type": cbx_row.get("code"),
        "subscription_price": subscription_price,
        "employee_price": employee_price,
        "parents": cbx_row.get("parents"),
        "previous": cbx_row.get("old_names"),
        "hiring_client_names": names_str,
        "hiring_client_count": hc_count,
        "is_in_relationship": is_in_relationship,
        "is_qualified": is_qualified,
        "matched_qstatus": matched_qstatus,
        "ratio_company": ratio_company,
        "ratio_address": ratio_address,
        "contact_match": contact_match,
        "cbx_assessment_level": cbx_row.get("assessment_level"),
        "new_product": cbx_row.get("new_product"),
    }


# -------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    result_file: Optional[str] = None
    error: Optional[str] = None
    created_at: str


class MatchConfig(BaseModel):
    min_company_ratio: int = 80
    min_address_ratio: int = 80


# -------------------------------------------------------------------
# Matching engine with CBX logic (legacy-exact, FastAPI-friendly)
# -------------------------------------------------------------------

class ContractorMatcher:
    def __init__(self, config: MatchConfig):
        self.config = config
        self.cbx_data: Optional[pd.DataFrame] = None

        # You can still keep indices for future optimizations if needed
        self.domain_index: Dict[str, list] = {}
        self.email_index: Dict[str, int] = {}
        self.company_index: Dict[str, list] = {}

    @staticmethod
    def normalize_email(email: Any) -> str:
        if not email or pd.isna(email):
            return ""
        return (
            str(email)
            .lower()
            .strip()
            .split(";")[0]
            .split(",")[0]
            .split("\n")[0]
            .strip()
        )

    @staticmethod
    def get_domain(email: str) -> str:
        return email.split("@")[1] if "@" in email else ""

    @staticmethod
    def is_generic_domain(domain: str) -> bool:
        return domain.lower() in GENERIC_DOMAINS

    @staticmethod
    def remove_generics(name: str) -> str:
        for word in GENERIC_COMPANY_NAME_WORDS:
            name = re.sub(r"\b" + re.escape(word) + r"\b", "", name)
        return name

    def clean_company_name(self, name: Any) -> str:
        if not name or pd.isna(name):
            return ""
        s = str(name).lower()
        s = s.replace(".", "").replace(",", "").strip()
        # remove (...) blocks
        s = re.sub(r"\([^()]*\)", "", s)
        s = self.remove_generics(s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def build_cbx_index(self, cbx_df: pd.DataFrame):
        """
        Build CBX indices and normalized fields.
        Ensures missing columns won't crash .apply().
        """
        self.cbx_data = cbx_df.copy()

        # ---- FIX: ensure required columns exist ----
        required_cols = [
            "email", "name_en", "name_fr", "postal_code", "address",
            "country", "old_names", "hiring_client_names",
            "hiring_client_qstatus", "modules", "parents",
        ]
        for col in required_cols:
            if col not in self.cbx_data.columns:
                self.cbx_data[col] = ""

        # Precompute normalized fields
        self.cbx_data["__email_norm"] = self.cbx_data["email"].apply(self.normalize_email)
        self.cbx_data["__domain"] = self.cbx_data["__email_norm"].apply(self.get_domain)
        self.cbx_data["__clean_name_en"] = self.cbx_data["name_en"].apply(self.clean_company_name)
        self.cbx_data["__clean_name_fr"] = self.cbx_data["name_fr"].apply(self.clean_company_name)

        self.cbx_data["__postal_no_space"] = (
            self.cbx_data["postal_code"]
            .astype(str)
            .str.replace(" ", "")
            .str.upper()
        )

        self.cbx_data["__address_clean"] = (
            self.cbx_data["address"]
            .astype(str)
            .str.lower()
            .str.replace(".", "", regex=False)
            .str.strip()
        )

        self.cbx_data["__country_up"] = (
            self.cbx_data["country"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # Optional indices
        self.domain_index = defaultdict(list)
        self.email_index = {}
        self.company_index = defaultdict(list)

        for idx, row in self.cbx_data.iterrows():
            email = row["__email_norm"]
            if email:
                domain = row["__domain"]
                self.email_index[email] = idx
                if not self.is_generic_domain(domain):
                    self.domain_index[domain].append(idx)

            clean_name = row["__clean_name_en"] or row["__clean_name_fr"]
            if clean_name:
                for word in clean_name.split()[:3]:
                    if len(word) > 3:
                        self.company_index[word].append(idx)

    def match_contractors(
        self, hc_df: pd.DataFrame, progress_callback=None
    ) -> pd.DataFrame:
        """
        Main matching logic: row-by-row, but using the exact same rules
        as the legacy script. This ignores the indices for correctness.
        """
        results = []
        total = len(hc_df)

        for idx, (_, hc_row) in enumerate(hc_df.iterrows()):
            if progress_callback and idx % 10 == 0:
                progress_callback(idx + 1)

            # Legacy: empty cells are '', not None
            hc: Dict[str, Any] = {
                k: ("" if pd.isna(v) else v) for k, v in hc_row.items()
            }

            hc_company = hc.get("contractor_name", "")
            clean_hc_company = self.clean_company_name(hc_company)

            hc_email = self.normalize_email(hc.get("contact_email", ""))
            hc_domain = self.get_domain(hc_email) if hc_email else ""
            hc_zip = str(hc.get("postal_code") or "").replace(" ", "").upper()
            hc_address = str(hc.get("address") or "").lower().replace(".", "").strip()
            hc_force_cbx = str(hc.get("force_cbx_id") or "")
            hc_country = (str(hc.get("country_iso2") or "")).upper()

            do_not_match = smart_boolean(hc.get("do_not_match"))
            matches: list[Dict[str, Any]] = []

            if not do_not_match:
                # 1) FORCE CBX ID (same as legacy)
                if hc_force_cbx:
                    forced = self.cbx_data[
                        self.cbx_data["id"].astype(str).str.strip() == hc_force_cbx
                    ]
                    if not forced.empty:
                        cbx_row = forced.iloc[0]
                        matches.append(
                            add_analysis_data(
                                hc,
                                cbx_row,
                                ratio_company=None,
                                ratio_address=None,
                                contact_match=True,
                            )
                        )
                else:
                    # 2) FULL SCAN OVER CBX (legacy behavior)
                    for _, cbx in self.cbx_data.iterrows():
                        cbx_email = self.normalize_email(cbx.get("email", ""))
                        cbx_domain = self.get_domain(cbx_email) if cbx_email else ""

                        # contact_match logic (identical to legacy)
                        if hc_email:
                            if self.is_generic_domain(hc_domain):
                                contact_match = cbx_email == hc_email
                            else:
                                contact_match = cbx_domain == hc_domain
                        else:
                            contact_match = False

                        cbx_zip = (str(cbx.get("postal_code") or "")).replace(
                            " ", ""
                        ).upper()
                        cbx_company_en = self.clean_company_name(cbx.get("name_en", ""))
                        cbx_company_fr = self.clean_company_name(cbx.get("name_fr", ""))
                        cbx_address = (
                            str(cbx.get("address") or "")
                            .lower()
                            .replace(".", "")
                            .strip()
                        )
                        cbx_country = (str(cbx.get("country") or "")).upper()

                        # --- Ratios (exact same formula as legacy) ---
                        if cbx_country != hc_country:
                            ratio_zip = 0.0
                            ratio_address = 0.0
                        else:
                            ratio_zip = (
                                fuzz.ratio(cbx_zip, hc_zip)
                                if cbx_zip and hc_zip
                                else 0.0
                            )
                            base_ratio_addr = (
                                fuzz.token_sort_ratio(cbx_address, hc_address)
                                if cbx_address and hc_address
                                else 0.0
                            )

                            # legacy combination logic:
                            if ratio_zip == 0:
                                ratio_address = base_ratio_addr
                            elif base_ratio_addr == 0:
                                ratio_address = ratio_zip
                            else:
                                ratio_address = base_ratio_addr * ratio_zip / 100.0

                        ratio_company_fr = (
                            fuzz.token_sort_ratio(cbx_company_fr, clean_hc_company)
                            if cbx_company_fr or clean_hc_company
                            else 0
                        )
                        ratio_company_en = (
                            fuzz.token_sort_ratio(cbx_company_en, clean_hc_company)
                            if cbx_company_en or clean_hc_company
                            else 0
                        )
                        ratio_company = (
                            ratio_company_fr
                            if ratio_company_fr > ratio_company_en
                            else ratio_company_en
                        )

                        # previous names
                        prev_names_str = cbx.get("old_names") or ""
                        ratio_previous = 0
                        if prev_names_str:
                            for item in str(prev_names_str).split(LIST_SEPARATOR):
                                if item in (
                                    cbx.get("name_en", ""),
                                    cbx.get("name_fr", ""),
                                ):
                                    # legacy skips if equal to main names
                                    continue
                                item_clean = self.clean_company_name(item)
                                if not item_clean:
                                    continue
                                r = fuzz.token_sort_ratio(item_clean, clean_hc_company)
                                if r > ratio_previous:
                                    ratio_previous = r

                        if ratio_previous > ratio_company:
                            ratio_company = ratio_previous

                        # --- legacy acceptance conditions ---
                        if (
                            contact_match
                            or (
                                ratio_company
                                >= float(self.config.min_company_ratio)
                                and ratio_address
                                >= float(self.config.min_address_ratio)
                            )
                        ):
                            matches.append(
                                add_analysis_data(
                                    hc,
                                    cbx,
                                    ratio_company=ratio_company,
                                    ratio_address=ratio_address,
                                    contact_match=contact_match,
                                )
                            )
                        elif ratio_company >= 95.0 or (
                            ratio_company >= float(self.config.min_company_ratio)
                            and ratio_address
                            >= float(self.config.min_address_ratio)
                        ):
                            matches.append(
                                add_analysis_data(
                                    hc,
                                    cbx,
                                    ratio_company=ratio_company,
                                    ratio_address=ratio_address,
                                    contact_match=contact_match,
                                )
                            )

            # ======= Post-processing: identical to your current port (and legacy) =======

            # Filter out DO NOT USE entries
            matches = [
                m
                for m in matches
                if "DO NOT USE" not in (str(m.get("company") or "").upper())
            ]

            # Prefer HC-name relationship
            hc_name_norm = norm_name(hc.get("hiring_client_name"))
            if hc_name_norm and matches:
                def has_hc_name(m: Dict[str, Any]) -> bool:
                    names = str(m.get("hiring_client_names") or "")
                    if not names:
                        return False
                    return any(
                        norm_name(x) == hc_name_norm
                        for x in names.split(LIST_SEPARATOR)
                    )

                hc_matches = [m for m in matches if has_hc_name(m)]
                if hc_matches:
                    matches = hc_matches

            # Prefer Active registration
            if matches:
                active_matches = [
                    m
                    for m in matches
                    if (m.get("registration_status") or "").strip() == "Active"
                ]
                if active_matches:
                    matches = active_matches

            # Sort matches: modules, hiring_client_count, address, company (same as legacy)
            if matches:
                matches = sorted(
                    matches,
                    key=lambda x: (
                        x.get("modules") or "",
                        x.get("hiring_client_count") or 0,
                        x.get("ratio_address") or 0,
                        x.get("ratio_company") or 0,
                    ),
                    reverse=True,
                )

            # Build analysis string for top 10 matches
            ids_lines = []
            for m in matches[:10]:
                line = (
                    f'{m.get("cbx_id")}, {m.get("company")}, {m.get("address")}, '
                    f'{m.get("city")}, {m.get("state")} {m.get("country")} {m.get("zip")}, '
                    f'{m.get("email")}, {m.get("first_name")} {m.get("last_name")} '
                    f'--> CR{m.get("ratio_company")}, AR{m.get("ratio_address")}, '
                    f'CM{m.get("contact_match")}, HCC{m.get("hiring_client_count")}, '
                    f'M[{m.get("modules")}]'
                )
                ids_lines.append(line)
            analysis_str = "\n".join(ids_lines)
            if matches:
                matches[0]["analysis"] = analysis_str

            uniques_cbx_id = set(m["cbx_id"] for m in matches) if matches else set()
            generic_domain_flag = hc_domain in GENERIC_DOMAINS
            match_count = len(uniques_cbx_id)
            match_count_with_hc = (
                len([i for i in matches if (i.get("hiring_client_count") or 0) > 0])
                if matches
                else 0
            )

            # Start building final row (HC + analysis)
            result_row: Dict[str, Any] = dict(hc)

            subscription_upgrade = False
            upgrade_price = 0.0
            prorated_upgrade_price = 0.0

            if matches and uniques_cbx_id:
                best = matches[0]

                # Merge CBX analysis data (except matched_qstatus, which is internal)
                for key, value in best.items():
                    if key != "matched_qstatus":
                        result_row[key] = value

                result_row["generic_domain"] = generic_domain_flag
                result_row["match_count"] = match_count
                result_row["match_count_with_hc"] = match_count_with_hc
                result_row["analysis"] = analysis_str

                # Subscription upgrade logic (same as legacy)
                base_sub_raw = hc.get("base_subscription_fee")
                if base_sub_raw in (None, "", 0):
                    base_subscription_fee = CBX_DEFAULT_STANDARD_SUBSCRIPTION
                    logger.warning(
                        f"No subscription fee defined for {hc.get('contractor_name')}, "
                        f"using default {base_subscription_fee}"
                    )
                else:
                    base_subscription_fee = to_float(base_sub_raw)

                current_sub_total = (
                    to_float(best.get("subscription_price"))
                    + to_float(best.get("employee_price"))
                )
                price_diff = base_subscription_fee - current_sub_total

                expiration_date = best.get("expiration_date")
                if (
                    price_diff > 0
                    and best.get("registration_status") == "Active"
                    and expiration_date
                    and current_sub_total > 0.0
                ):
                    subscription_upgrade = True
                    upgrade_price = price_diff
                    now = datetime.now()
                    if expiration_date > now:
                        delta = expiration_date - now
                        days = delta.days if delta.days < 365 else 365
                        prorated_upgrade_price = days / 365 * upgrade_price
                    else:
                        prorated_upgrade_price = upgrade_price

                    if smart_boolean(hc.get("is_association_fee")):
                        upgrade_price += 100.0
                        prorated_upgrade_price += 100.0

                # account type overrides
                account_type = (best.get("account_type") or "").strip().lower()
                if account_type in ("elearning", "plan_nord", "portail_pfr", "special"):
                    subscription_upgrade = True
                    upgrade_price = base_subscription_fee
                    prorated_upgrade_price = base_subscription_fee

                # assessment level upgrade
                if (
                    parse_assessment_level(best.get("cbx_assessment_level"))
                    < parse_assessment_level(hc.get("assessment_level"))
                ):
                    subscription_upgrade = True
                    if prorated_upgrade_price == 0:
                        prorated_upgrade_price = (
                            upgrade_price or base_subscription_fee
                        )

            else:
                # No matches -> still add analysis columns with empty CBX info
                result_row["generic_domain"] = generic_domain_flag
                result_row["match_count"] = 0
                result_row["match_count_with_hc"] = 0
                result_row["analysis"] = analysis_str

            # Create in CBX? (same as legacy)
            ambiguous = smart_boolean(hc.get("ambiguous"))
            create_in_cbx = False if match_count and not ambiguous else True

            # Decide action (same mapping as legacy `action`)
            if matches and uniques_cbx_id:
                best = matches[0]
                action_value = action_for_row(
                    hc,
                    best,
                    create_in_cbx=create_in_cbx,
                    subscription_update=subscription_upgrade,
                    expiration_date=best.get("expiration_date"),
                    is_qualified=best.get("is_qualified", False),
                )
            else:
                action_value = action_for_row(
                    hc,
                    {},
                    create_in_cbx=True,
                    subscription_update=False,
                    expiration_date=None,
                    is_qualified=False,
                )

            result_row["subscription_upgrade"] = subscription_upgrade
            result_row["upgrade_price"] = (
                round(upgrade_price, 2) if upgrade_price else 0.0
            )
            result_row["prorated_upgrade_price"] = (
                round(prorated_upgrade_price, 2) if prorated_upgrade_price else 0.0
            )
            result_row["create_in_cbx"] = create_in_cbx
            result_row["action"] = action_value
            result_row["row_index"] = idx + 1

            results.append(result_row)

        return pd.DataFrame(results)


# Thread pool for jobs
EXECUTOR = ThreadPoolExecutor(max_workers=2)


def process_job(job_id: str, cbx_path: Path, hc_path: Path, config: MatchConfig):
    try:
        t0 = time.time()
        logger.info(f"[{job_id}] Starting processing")

        # ---- Read CBX ----
        update_job(job_id, status="processing", message="Reading CBX...", progress=0.05)
        if cbx_path.suffix.lower() in (".xlsx", ".xls"):
            cbx_df = pd.read_excel(cbx_path, engine="openpyxl")
        else:
            cbx_df = pd.read_csv(cbx_path)
        logger.info(f"[{job_id}] CBX read ({len(cbx_df)} rows)")

        # ---- Read HC ----
        update_job(job_id, message="Reading HC...", progress=0.10)
        if hc_path.suffix.lower() in (".xlsx", ".xls"):
            hc_df = pd.read_excel(hc_path, engine="openpyxl")
        else:
            hc_df = pd.read_csv(hc_path)
        logger.info(f"[{job_id}] HC read ({len(hc_df)} rows)")

        # Drop completely empty rows (same spirit as legacy script)
        cbx_df_clean = cbx_df.dropna(how="all").copy()
        hc_df_clean = hc_df.dropna(how="all").copy()

        # ---- Build matcher / index ----
        update_job(job_id, message="Building index...", progress=0.15)
        matcher = ContractorMatcher(config)
        matcher.build_cbx_index(cbx_df_clean)

        total = len(hc_df_clean)
        update_job(job_id, message=f"Matching {total} records...", progress=0.20)

        def progress_cb(i: int):
            if total:
                p = 0.20 + 0.70 * (i / total)
                update_job(job_id, progress=p, message=f"{i}/{total}")

        # ---- Matching ----
        results = matcher.match_contractors(hc_df_clean, progress_cb)
        logger.info(f"[{job_id}] Matching produced {len(results)} rows")

        # ================================================================
        #   Make the columns look like the legacy Excel ("all" sheet)
        # ================================================================

        # 1) Rename internal CBX fields -> legacy cbx_* fields
        rename_map = {
            "company": "cbx_contractor",
            "address": "cbx_street",
            "city": "cbx_city",
            "state": "cbx_state",
            "zip": "cbx_zip",
            "country": "cbx_country",
            "expiration_date": "cbx_expiration_date",
            "email": "cbx_email",
            "first_name": "cbx_first_name",
            "last_name": "cbx_last_name",
            "account_type": "cbx_account_type",
            "subscription_price": "cbx_subscription_fee",
            "employee_price": "cbx_employee_price",
            "subscription_upgrade": "is_subscription_upgrade",
            "row_index": "index",
        }
        rename_map = {k: v for k, v in rename_map.items() if k in results.columns}
        results = results.rename(columns=rename_map)

        # 2) Column ordering = HC columns first, then analysis headers in legacy order
        hc_columns = list(hc_df_clean.columns)

        analysis_headers = ANALYSIS_HEADERS  # from your constants at top

        ordered_cols: list[str] = []

        # a) All HC columns in original order
        for col in hc_columns:
            if col in results.columns and col not in ordered_cols:
                ordered_cols.append(col)

        # b) Legacy analysis headers in exact order
        for col in analysis_headers:
            if col in results.columns and col not in ordered_cols:
                ordered_cols.append(col)

        # c) Any leftover / debug columns at the end
        for col in results.columns:
            if col not in ordered_cols:
                ordered_cols.append(col)

        results = results.reindex(columns=ordered_cols)

        # ---- Write Excel with legacy-like sheets ----
        update_job(job_id, progress=0.95, message="Saving...")
        out_file = OUTPUT_DIR / f"{job_id}_results.xlsx"


        with pd.ExcelWriter(out_file, engine="openpyxl", mode="w") as writer:
            # Main sheet: legacy calls it "all"
            results.to_excel(writer, sheet_name="all", index=False)

            # Per-action sheets (same names as original script)
            action_values = [
                "onboarding",
                "association_fee",
                "re_onboarding",
                "subscription_upgrade",
                "ambiguous_onboarding",
                "restore_suspended",
                "activation_link",
                "already_qualified",
                "add_questionnaire",
                "missing_info",
                "follow_up_qualification",
            ]

            if "action" in results.columns:
                for act in action_values:
                    mask = results["action"] == act
                    if mask.any():
                        results.loc[mask].to_excel(writer, sheet_name=act, index=False)

        logger.info(f"[{job_id}] Saved to {out_file}")

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Done!",
            result_file=out_file.name,
        )

    except Exception as e:
        logger.exception(f"[{job_id}] FAILED")
        update_job(job_id, status="failed", message=str(e), error=str(e))




# -------------------------------------------------------------------
# API endpoints
# -------------------------------------------------------------------

@app.post("/api/match", response_model=JobStatus)
async def match(
    cbx_file: UploadFile = File(...),
    hc_file: UploadFile = File(...),
    min_company_ratio: int = Form(80),
    min_address_ratio: int = Form(80),
):
    """
    Ultra-fast upload + async processing.
    hc_file  = contractor list from hiring client
    cbx_file = CBX database export
    """
    t_start = time.time()
    logger.info("========== NEW REQUEST ==========")
    logger.info(f"Files: {cbx_file.filename}, {hc_file.filename}")

    job_id = str(uuid.uuid4())[:8]  # Shorter ID for logs

    cbx_path = UPLOAD_DIR / f"{job_id}_cbx.{cbx_file.filename.split('.')[-1]}"
    hc_path = UPLOAD_DIR / f"{job_id}_hc.{hc_file.filename.split('.')[-1]}"

    # Save files to disk (fast path with shutil)
    logger.info("Saving CBX...")
    t1 = time.time()
    with open(cbx_path, "wb") as f:
        shutil.copyfileobj(cbx_file.file, f, length=1024 * 1024)
    logger.info(
        f"CBX saved in {time.time()-t1:.3f}s ({cbx_path.stat().st_size/1024/1024:.2f} MB)"
    )

    logger.info("Saving HC...")
    t1 = time.time()
    with open(hc_path, "wb") as f:
        shutil.copyfileobj(hc_file.file, f, length=1024 * 1024)
    logger.info(
        f"HC saved in {time.time()-t1:.3f}s ({hc_path.stat().st_size/1024/1024:.2f} MB)"
    )

    logger.info(f"TOTAL UPLOAD TIME: {time.time()-t_start:.3f}s")

    # Create job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0.01,
        "message": "Starting...",
        "created_at": datetime.now().isoformat(),
        "result_file": None,
        "error": None,
    }

    # Start processing in background thread
    config = MatchConfig(
        min_company_ratio=min_company_ratio, min_address_ratio=min_address_ratio
    )
    loop = asyncio.get_running_loop()
    loop.run_in_executor(EXECUTOR, process_job, job_id, cbx_path, hc_path, config)

    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}/download")
async def download(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404)
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Not completed")
    file_path = OUTPUT_DIR / job["result_file"]
    return FileResponse(file_path, filename=job["result_file"])


@app.get("/api/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
