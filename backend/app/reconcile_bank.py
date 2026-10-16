"""Read-only bank preflight; explicitly apply the reviewed pg-m089 correction."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json

from sqlalchemy import select

from .benchmark import import_pack, _translation_manifest, _validate_pack_translations
from .config import ROOT_DIR, get_settings
from .db import get_session_factory
from .errors import AppError
from .models import Question
from .repositories import AccountRepository, CurriculumRepository, QuestionRepository
from .schemas import QuestionUpsertRequest
from .services.question_service import get_question, _validation_missing
from .services.question_localization import translation_is_current, normalized_translation
from .services.sandbox_runner import SandboxRunner


def load_packs():
    return [json.loads((ROOT_DIR / 'db' / name).read_text(encoding='utf-8'))
            for name in ('benchmark_pack.json', 'sql_knowledge_pack.json', 'postgres_knowledge_pack.json')]


def normalized(payload):
    value = payload.model_dump()
    value.pop('translations', None)
    for field in ('concept_ids', 'required_concept_ids', 'options', 'datasets', 'rubrics'):
        value[field] = sorted(value[field], key=lambda row: json.dumps(row, sort_keys=True, default=str))
    return value


def source_payload(db, item):
    repo = CurriculumRepository(db)
    codes = set(item['concept_codes']) | set(item.get('required_concept_codes', []))
    concepts = {code: repo.find_concept_by_code(code) for code in codes}
    if any(value is None for value in concepts.values()):
        raise AppError(409, 'reconciliation_missing_concept', 'Import curriculum before reconciling existing questions')
    return QuestionUpsertRequest(**{**item,
        'concept_ids': [concepts[code].concept_id for code in item['concept_codes']],
        'required_concept_ids': [concepts[code].concept_id for code in item.get('required_concept_codes', [])]})


def current_payload(db, question):
    detail = get_question(db, question.question_id)
    return QuestionUpsertRequest(**{**detail.model_dump(),
        'concept_ids': [tag.concept_id for tag in detail.concepts if tag.confirmed],
        'required_concept_ids': [tag.concept_id for tag in detail.concepts if tag.confirmed and tag.is_required]})


def reviewed_correction_matches(db, question, item):
    manifest = json.loads((ROOT_DIR / 'db/pg_m089_reconciliation.json').read_text(encoding='utf-8'))
    if item['key'] != manifest['question_key'] or question.version_no != manifest['expected_version']:
        return False
    if question.status != 'validated' or question.family_id is not None:
        return False
    if any(QuestionRepository(db).reference_counts(question.question_id).values()):
        return False  # Referenced versions require separate historical review.
    before = manifest['before']
    after = deepcopy(before)
    after['explanation'] = manifest['after']['explanation']
    for option in after['options']:
        option['option_text'] = manifest['after']['option_texts'].get(option['option_label'], option['option_text'])
    return (normalized(current_payload(db, question)) == normalized(source_payload(db, before))
            and normalized(source_payload(db, item)) == normalized(source_payload(db, after)))


def translation_value(row):
    return {'prompt': row.prompt, 'explanation': row.explanation,
            'option_texts': row.option_texts or {}, 'rubrics': row.rubrics or {}}


def preflight(db, packs=None):
    """No writes. Refuse collisions, owner changes and unexpected lifecycle drift."""
    packs = packs if packs is not None else load_packs()
    repo = QuestionRepository(db)
    result = {'matched_questions': 0, 'matched_translations': 0, 'stale_translations': 0,
              'missing_questions': [], 'missing_translations': [], 'extra_questions': [],
              'corrections': [], 'conflicts': []}
    seen = set()
    for pack in packs:
        translations = _translation_manifest(pack)
        _validate_pack_translations(pack, translations)
        for item in pack['questions']:
            matches = [q for q in repo.search(q=item['prompt']) if q.prompt == item['prompt']]
            if len(matches) != 1:
                result['missing_questions' if not matches else 'conflicts'].append(item['key'])
                continue
            question = repo.get_detail(matches[0].question_id)
            seen.add(question.question_id)
            if question.status != item.get('status', 'validated'):
                result['conflicts'].append({'key': item['key'], 'reason': 'lifecycle differs'})
                continue
            if normalized(current_payload(db, question)) == normalized(source_payload(db, item)):
                result['matched_questions'] += 1
            elif reviewed_correction_matches(db, question, item):
                result['corrections'].append({'key': item['key'], 'question_id': question.question_id,
                    'from_version': question.version_no, 'to_version': question.version_no + 1,
                    'fields': ['options.C.option_text', 'explanation']})
            else:
                result['conflicts'].append({'key': item['key'], 'question_id': question.question_id,
                                            'reason': 'unreviewed content/version/references'})
            translated = translations['questions'][item['key']]
            expected = normalized_translation(translated)
            row = next((r for r in question.translations if r.locale == 'vi'), None)
            if row is None:
                result['missing_translations'].append(item['key'])
            elif translation_value(row) != expected:
                result['conflicts'].append({'key': item['key'], 'reason': 'translation content differs'})
            elif not translation_is_current(question, row):
                result['stale_translations'] += 1
            else:
                result['matched_translations'] += 1
    result['extra_questions'] = sorted(set(db.scalars(select(Question.question_id))) - seen)
    return result


def apply_correction(db, question_id, item):
    repo = QuestionRepository(db)
    repo.lock_question(question_id)
    question = repo.get_detail(question_id)
    if not reviewed_correction_matches(db, question, item):
        raise AppError(409, 'reconciliation_conflict', 'Current row is not the exact unreferenced reviewed version')
    # Preserve both question and option identities. No scoring fields change.
    question.explanation = item['explanation']
    texts = {row['option_label']: row['option_text'] for row in item['options']}
    for option in question.options:
        option.option_text = texts[option.option_label]
    question.version_no += 1
    question.updated_at = datetime.now(timezone.utc)
    db.flush()
    if _validation_missing(repo, question):
        db.rollback()
        raise AppError(422, 'reconciliation_invalid', 'Corrected question failed ordinary bank validation')
    # Caller commits through the ordinary pack importer with its translation.


def reconcile(db, admin, runner, packs=None):
    if not any(role.role_name == 'Administrator' for role in admin.roles):
        raise AppError(403, 'admin_required', 'Reconciliation requires an administrator')
    packs = packs if packs is not None else load_packs()
    plan = preflight(db, packs)
    if plan['conflicts'] or plan['missing_questions'] or plan['extra_questions']:
        raise AppError(409, 'reconciliation_conflict', 'Preflight requires owner review', details=[plan])
    sources = {item['key']: item for pack in packs for item in pack['questions']}
    for correction in plan['corrections']:
        apply_correction(db, correction['question_id'], sources[correction['key']])
    for pack in packs:
        import_pack(db, admin, runner, pack)
    return preflight(db, packs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply only reviewed changes after whole-bank preflight')
    parser.add_argument('--admin-email', help='Existing administrator; required with --apply')
    args = parser.parse_args()
    with get_session_factory()() as db:
        if args.apply:
            admin = AccountRepository(db).find_by_email((args.admin_email or '').strip().lower())
            if admin is None:
                raise SystemExit('Existing administrator required with --apply')
            result = reconcile(db, admin, SandboxRunner(get_settings()))
        else:
            result = preflight(db)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['conflicts'] or result['missing_questions'] or result['extra_questions']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
