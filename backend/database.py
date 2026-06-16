import httpx
import os
from dotenv import load_dotenv
from typing import Optional, Any

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

BASE = f"{SUPABASE_URL}/rest/v1"


class SupabaseResult:
    def __init__(self, data):
        self.data = data


class SupabaseQuery:
    def __init__(self, table: str):
        self.table = table
        self._select = "*"
        self._filters = []
        self._order = None
        self._limit = None
        self._insert_data = None
        self._update_data = None
        self._delete = False
        self._upsert = False
        self._or = None

    def select(self, cols: str):
        self._select = cols
        return self

    def insert(self, data: dict):
        self._insert_data = data
        return self

    def update(self, data: dict):
        self._update_data = data
        return self

    def delete(self):
        self._delete = True
        return self

    def upsert(self, data: dict):
        self._insert_data = data
        self._upsert = True
        return self

    def eq(self, col: str, val: Any):
        if val is None:
            self._filters.append(f"{col}=is.null")
        else:
            self._filters.append(f"{col}=eq.{val}")
        return self

    def neq(self, col: str, val: Any):
        self._filters.append(f"{col}=neq.{val}")
        return self

    def gt(self, col: str, val: Any):
        self._filters.append(f"{col}=gt.{val}")
        return self

    def gte(self, col: str, val: Any):
        self._filters.append(f"{col}=gte.{val}")
        return self

    def lt(self, col: str, val: Any):
        self._filters.append(f"{col}=lt.{val}")
        return self

    def lte(self, col: str, val: Any):
        self._filters.append(f"{col}=lte.{val}")
        return self

    def in_(self, col: str, vals: list):
        vals_str = ",".join(str(v) for v in vals)
        self._filters.append(f"{col}=in.({vals_str})")
        return self

    def is_(self, col: str, val):
        self._filters.append(f"{col}=is.{val}")
        return self

    def or_(self, condition: str):
        self._or = condition
        return self

    def order(self, col: str, desc: bool = False):
        self._order = f"{col}.{'desc' if desc else 'asc'}"
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def _build_url(self):
        url = f"{BASE}/{self.table}"
        params = []
        if self._insert_data is None and self._update_data is None and not self._delete:
            params.append(f"select={self._select}")
        for f in self._filters:
            col, expr = f.split("=", 1)
            params.append(f"{col}={expr}")
        if self._or:
            params.append(f"or=({self._or})")
        if self._order:
            params.append(f"order={self._order}")
        if self._limit:
            params.append(f"limit={self._limit}")
        if params:
            url += "?" + "&".join(params)
        return url

    def _build_filter_params(self):
        params = {}
        for f in self._filters:
            col, expr = f.split("=", 1)
            params[col] = expr
        if self._or:
            params["or"] = f"({self._or})"
        if self._order:
            params["order"] = self._order
        if self._limit:
            params["limit"] = str(self._limit)
        return params

    def execute(self) -> SupabaseResult:
        with httpx.Client(timeout=30) as client:
            if self._insert_data is not None and not self._upsert:
                r = client.post(f"{BASE}/{self.table}", headers=HEADERS, json=self._insert_data)
                r.raise_for_status()
                data = r.json()
                return SupabaseResult(data if isinstance(data, list) else [data])

            elif self._upsert:
                h = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
                r = client.post(f"{BASE}/{self.table}", headers=h, json=self._insert_data)
                r.raise_for_status()
                data = r.json()
                return SupabaseResult(data if isinstance(data, list) else [data])

            elif self._update_data is not None:
                params = self._build_filter_params()
                params["select"] = self._select
                r = client.patch(f"{BASE}/{self.table}", headers=HEADERS, params=params, json=self._update_data)
                r.raise_for_status()
                data = r.json()
                return SupabaseResult(data if isinstance(data, list) else [data])

            elif self._delete:
                params = self._build_filter_params()
                r = client.delete(f"{BASE}/{self.table}", headers=HEADERS, params=params)
                r.raise_for_status()
                return SupabaseResult([])

            else:
                params = self._build_filter_params()
                params["select"] = self._select
                r = client.get(f"{BASE}/{self.table}", headers=HEADERS, params=params)
                r.raise_for_status()
                return SupabaseResult(r.json())


class SupabaseTable:
    def __init__(self, table: str):
        self.table = table

    def select(self, cols: str = "*") -> SupabaseQuery:
        return SupabaseQuery(self.table).select(cols)

    def insert(self, data: dict) -> SupabaseQuery:
        return SupabaseQuery(self.table).insert(data)

    def update(self, data: dict) -> SupabaseQuery:
        return SupabaseQuery(self.table).update(data)

    def delete(self) -> SupabaseQuery:
        return SupabaseQuery(self.table).delete()

    def upsert(self, data: dict) -> SupabaseQuery:
        return SupabaseQuery(self.table).upsert(data)


class SupabaseClient:
    def table(self, name: str) -> SupabaseTable:
        return SupabaseTable(name)


supabase = SupabaseClient()
