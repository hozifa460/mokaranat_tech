"""
Hardware Repository for persisting and retrieving specs and comparisons.
Clean Architecture - Layer: Repository / Data Access
"""

import json
from typing import List, Optional
from core.domain.models import HardwareSpec, ComparisonDocument
from core.repository.database import db_session, get_db_connection


class HardwareRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def _get_session(self):
        if self.db_path:
            return db_session(self.db_path)
        return db_session()

    def upsert_hardware_spec(self, spec: HardwareSpec) -> None:
        """Insert or update a hardware specification record."""
        query = """
        INSERT INTO hardware_specs (
            id, slug, name, category, brand, release_year, launch_msrp_usd,
            architecture, process_node_nm, tdp_w, raw_specs_json,
            benchmark_index, gaming_scores_json, ray_tracing_score,
            efficiency_score, features_json, pcie_interface, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            slug=excluded.slug,
            name=excluded.name,
            category=excluded.category,
            brand=excluded.brand,
            release_year=excluded.release_year,
            launch_msrp_usd=excluded.launch_msrp_usd,
            architecture=excluded.architecture,
            process_node_nm=excluded.process_node_nm,
            tdp_w=excluded.tdp_w,
            raw_specs_json=excluded.raw_specs_json,
            benchmark_index=excluded.benchmark_index,
            gaming_scores_json=excluded.gaming_scores_json,
            ray_tracing_score=excluded.ray_tracing_score,
            efficiency_score=excluded.efficiency_score,
            features_json=excluded.features_json,
            pcie_interface=excluded.pcie_interface,
            updated_at=CURRENT_TIMESTAMP;
        """
        with self._get_session() as conn:
            conn.execute(
                query,
                (
                    spec.id,
                    spec.slug,
                    spec.name,
                    spec.category,
                    spec.brand,
                    spec.release_year,
                    spec.launch_msrp_usd,
                    spec.architecture,
                    spec.process_node_nm,
                    spec.tdp_w,
                    json.dumps(spec.raw_specs, ensure_ascii=False),
                    spec.benchmark_index,
                    json.dumps(spec.gaming_scores, ensure_ascii=False),
                    spec.ray_tracing_score,
                    spec.efficiency_score,
                    json.dumps(spec.features, ensure_ascii=False),
                    spec.pcie_interface
                )
            )

    def get_hardware_by_id(self, item_id: str) -> Optional[HardwareSpec]:
        """Retrieve hardware spec by unique ID."""
        query = "SELECT * FROM hardware_specs WHERE id = ?;"
        with self._get_session() as conn:
            row = conn.execute(query, (item_id,)).fetchone()
            if not row:
                return None
            return self._row_to_spec(row)

    def get_hardware_by_slug(self, slug: str) -> Optional[HardwareSpec]:
        """Retrieve hardware spec by slug."""
        query = "SELECT * FROM hardware_specs WHERE slug = ?;"
        with self._get_session() as conn:
            row = conn.execute(query, (slug,)).fetchone()
            if not row:
                return None
            return self._row_to_spec(row)

    def list_by_category(self, category: str) -> List[HardwareSpec]:
        """List all hardware specs in a specific category ordered by benchmark_index desc."""
        query = "SELECT * FROM hardware_specs WHERE category = ? ORDER BY benchmark_index DESC;"
        with self._get_session() as conn:
            rows = conn.execute(query, (category,)).fetchall()
            return [self._row_to_spec(row) for row in rows]

    def list_all_hardware(self) -> List[HardwareSpec]:
        """List all hardware items in the database."""
        query = "SELECT * FROM hardware_specs ORDER BY category, benchmark_index DESC;"
        with self._get_session() as conn:
            rows = conn.execute(query).fetchall()
            return [self._row_to_spec(row) for row in rows]

    def save_comparison_cache(self, doc: ComparisonDocument) -> None:
        """Cache a generated comparison document in SQLite."""
        query = """
        INSERT INTO comparisons_cache (slug, category, item_a_id, item_b_id, data_json, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
            category=excluded.category,
            item_a_id=excluded.item_a_id,
            item_b_id=excluded.item_b_id,
            data_json=excluded.data_json,
            created_at=CURRENT_TIMESTAMP;
        """
        with self._get_session() as conn:
            conn.execute(
                query,
                (
                    doc.slug,
                    doc.category,
                    doc.item_a.id,
                    doc.item_b.id,
                    doc.model_dump_json()
                )
            )

    def get_cached_comparison(self, slug: str) -> Optional[ComparisonDocument]:
        """Retrieve cached comparison document by slug."""
        query = "SELECT data_json FROM comparisons_cache WHERE slug = ?;"
        with self._get_session() as conn:
            row = conn.execute(query, (slug,)).fetchone()
            if not row:
                return None
            return ComparisonDocument.model_validate_json(row["data_json"])

    def list_all_comparisons(self) -> List[ComparisonDocument]:
        """Retrieve all cached comparisons."""
        query = "SELECT data_json FROM comparisons_cache ORDER BY created_at DESC;"
        with self._get_session() as conn:
            rows = conn.execute(query).fetchall()
            return [ComparisonDocument.model_validate_json(r["data_json"]) for r in rows]

    @staticmethod
    def _row_to_spec(row) -> HardwareSpec:
        raw_specs = json.loads(row["raw_specs_json"])
        pcie_val = None
        if "pcie_interface" in row.keys() and row["pcie_interface"]:
            pcie_val = row["pcie_interface"]
        elif "pcie_interface" in raw_specs:
            pcie_val = raw_specs["pcie_interface"]

        return HardwareSpec(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            category=row["category"],
            brand=row["brand"],
            release_year=row["release_year"],
            launch_msrp_usd=row["launch_msrp_usd"],
            architecture=row["architecture"],
            process_node_nm=row["process_node_nm"],
            tdp_w=row["tdp_w"],
            raw_specs=raw_specs,
            benchmark_index=row["benchmark_index"],
            gaming_scores=json.loads(row["gaming_scores_json"]),
            ray_tracing_score=row["ray_tracing_score"],
            efficiency_score=row["efficiency_score"],
            features=json.loads(row["features_json"]),
            pcie_interface=pcie_val
        )
