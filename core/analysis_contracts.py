from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class RequiredParams(TypedDict, total=False):
    date: Optional[str]
    process_name: Optional[Any]
    oper_num: Optional[Any]
    pkg_type1: Optional[Any]
    pkg_type2: Optional[Any]
    product_name: Optional[str]
    line_name: Optional[str]
    mode: Optional[Any]
    den: Optional[Any]
    tech: Optional[Any]
    lead: Optional[str]
    mcp_no: Optional[str]
    group_by: Optional[str]
    metrics: List[str]
    date_inherited: bool
    process_inherited: bool
    oper_num_inherited: bool
    pkg_type1_inherited: bool
    pkg_type2_inherited: bool
    product_inherited: bool
    line_inherited: bool
    mode_inherited: bool
    den_inherited: bool
    tech_inherited: bool
    lead_inherited: bool
    mcp_no_inherited: bool


class DatasetProfile(TypedDict):
    columns: List[str]
    row_count: int
    sample_rows: List[Dict[str, Any]]


class PreprocessPlan(TypedDict, total=False):
    intent: str
    operations: List[str]
    output_columns: List[str]
    group_by_columns: List[str]
    partition_by_columns: List[str]
    filters: List[Dict[str, Any]]
    sort_by: str
    sort_order: str
    top_n: int
    top_n_per_group: int
    metric_column: str
    warnings: List[str]
    code: str
    source: str


class DomainNote(TypedDict, total=False):
    id: str
    title: str
    created_at: str
    raw_text: str
    notes: List[str]


class DerivedMetricRule(TypedDict, total=False):
    name: str
    display_name: str
    synonyms: List[str]
    required_datasets: List[str]
    required_columns: List[str]
    source_columns: List[Dict[str, str]]
    calculation_mode: str
    output_column: str
    default_group_by: List[str]
    condition: str
    decision_rule: str
    formula: str
    pandas_hint: str
    description: str
    source: str


class JoinRule(TypedDict, total=False):
    name: str
    base_dataset: str
    join_dataset: str
    join_type: str
    join_keys: List[str]
    description: str
    source: str


class RuleParseResult(TypedDict, total=False):
    success: bool
    payload: Dict[str, Any]
    issues: List[Dict[str, str]]
    can_save: bool
