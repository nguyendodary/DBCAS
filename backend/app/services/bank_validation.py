"""Question configuration checks shared by bank activation and AI review."""
import json
from functools import lru_cache
from types import SimpleNamespace
from .dataset_setup import validated_setup_statements
from .sql_result import parse_expected, compare
from .sql_features import detect_features
from .sql_validator import validate_learner_sql
from .sandbox_runner import SandboxError


def sql_fixture_problems(datasets, reference_answer, required_features=()):
    key = tuple((d.dataset_name, d.setup_sql, json.dumps(d.expected_result, sort_keys=True), d.is_edge_case)
                for d in datasets)
    return list(_cached_fixture_problems(key, reference_answer, tuple(required_features)))


@lru_cache(maxsize=256)
def _cached_fixture_problems(key, reference_answer, required_features):
    datasets = [SimpleNamespace(dataset_name=name, setup_sql=setup,
        expected_result=json.loads(expected), is_edge_case=edge) for name, setup, expected, edge in key]
    problems = []
    if len(datasets) < 2:
        problems.append("SQL needs at least two test datasets")
    if not any(d.is_edge_case for d in datasets):
        problems.append("SQL needs an edge-case dataset")
    if not isinstance(reference_answer, str) or not reference_answer.strip():
        problems.append("SQL needs a reference answer")
    elif validate_learner_sql(reference_answer):
        problems.append("SQL reference answer must be a permitted PostgreSQL SELECT")
    names = set()
    for dataset in datasets:
        if dataset.dataset_name in names:
            problems.append("SQL dataset names must be unique")
        names.add(dataset.dataset_name)
        if parse_expected(dataset.expected_result) is None:
            problems.append(f"Dataset '{dataset.dataset_name}' has an invalid expected result")
        try:
            validated_setup_statements(dataset.setup_sql)
        except ValueError as error:
            problems.append(f"Dataset '{dataset.dataset_name}': {error}")
    features = detect_features(reference_answer or "")
    for feature in required_features:
        if not feature:
            problems.append("Required SQL concepts need explicit SQL technique metadata")
        elif feature not in features:
            problems.append(f"Reference answer must demonstrate required technique '{feature}'")
    return tuple(problems)


def verify_sql_fixtures(runner, datasets, reference_answer):
    """Execute controlled setup and reference queries before eligibility."""
    problems = []
    for dataset in datasets:
        schema = None
        try:
            schema = runner.provision_dataset(dataset.setup_sql)
            result = runner.execute(reference_answer, schema=schema)
            expected = parse_expected(dataset.expected_result)
            if not result.success or expected is None or compare(
                    result.columns, result.rows, expected, result.column_types).status != "passed":
                problems.append(f"Dataset '{dataset.dataset_name}' does not match its reference result")
        except SandboxError as error:
            problems.append(f"Dataset '{dataset.dataset_name}' cannot be verified ({error.code})")
        finally:
            if schema:
                runner.drop_dataset(schema)
    return problems
