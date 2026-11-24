// Assessment modes. The backend owns the authoritative constraints; these
// helpers keep the browser selection inside them before a start request.
export const FIXED = 'FIXED'
export const ADAPTIVE = 'ADAPTIVE'

// Mirrors PracticeStart.typed_question_limits for the adaptive branch:
// bank-only, one concept, one starting band, MCQ-only, 3..50 questions.
export const ADAPTIVE_MIN_QUESTIONS = 3
export const ADAPTIVE_MAX_QUESTIONS = 50

// Mirrors the FIXED branch of PracticeStart.typed_question_limits. The mixed
// caps apply only when at least two question types are selected; a single-type
// test uses the larger single-type cap.
export const FIXED_SINGLE_LIMITS = Object.freeze({ mcq: 50, sql: 5, essay: 10 })
export const FIXED_MIXED_LIMITS = Object.freeze({ mcq: 20, sql: 2, essay: 3 })
export const FIXED_MIXED_TOTAL_LIMIT = 25
export const FIXED_QUESTION_TYPES = Object.freeze(['mcq', 'sql', 'essay'])
export const FIXED_DEFAULT_MIX = Object.freeze({ mcq: 10, sql: 2, essay: 1 })

export function clampAdaptiveCount(value, fallback = ADAPTIVE_MIN_QUESTIONS) {
  const parsed = Number(value)
  if (!Number.isInteger(parsed)) return fallback
  return Math.min(ADAPTIVE_MAX_QUESTIONS, Math.max(ADAPTIVE_MIN_QUESTIONS, parsed))
}

export function isAdaptiveResult(session) {
  return Boolean(
    session && (session.result_kind === 'estimated_ability' || session.runner_mode === 'adaptive'),
  )
}

export function normalizeFixedMix(mix = FIXED_DEFAULT_MIX) {
  return Object.fromEntries(FIXED_QUESTION_TYPES.map((kind) => [kind, Number(mix?.[kind] ?? 0)]))
}

export function fixedMixTotal(mix) {
  const counts = normalizeFixedMix(mix)
  return FIXED_QUESTION_TYPES.reduce(
    (total, kind) => total + (Number.isFinite(counts[kind]) ? counts[kind] : 0),
    0,
  )
}

// Returns structured errors so the UI can translate one shared contract.
export function validateFixedMix(mix) {
  const counts = normalizeFixedMix(mix)
  const errors = []
  if (FIXED_QUESTION_TYPES.some((kind) => !Number.isInteger(counts[kind]) || counts[kind] < 0)) {
    errors.push({ code: 'invalid' })
  }
  const active = FIXED_QUESTION_TYPES.filter((kind) => counts[kind] > 0)
  const total = FIXED_QUESTION_TYPES.reduce(
    (sum, kind) => sum + (Number.isFinite(counts[kind]) ? counts[kind] : 0),
    0,
  )
  if (!errors.length) {
    if (!active.length) {
      errors.push({ code: 'empty' })
    } else if (active.length === 1) {
      const kind = active[0]
      if (counts[kind] > FIXED_SINGLE_LIMITS[kind]) {
        errors.push({ code: 'single_limit', kind, limit: FIXED_SINGLE_LIMITS[kind] })
      }
    } else {
      for (const kind of active) {
        if (counts[kind] > FIXED_MIXED_LIMITS[kind]) {
          errors.push({ code: 'type_limit', kind, limit: FIXED_MIXED_LIMITS[kind] })
        }
      }
      if (total > FIXED_MIXED_TOTAL_LIMIT) {
        errors.push({ code: 'total_limit', limit: FIXED_MIXED_TOTAL_LIMIT })
      }
    }
  }
  return { counts, total, active, errors, valid: errors.length === 0 }
}

export function buildPracticePayload({ style, selected, bands, mix, requestId }) {
  const typed = validateFixedMix(mix)
  if (style === ADAPTIVE) {
    return {
      concept_ids: selected.slice(0, 1),
      difficulties: bands.slice(0, 1),
      source: 'ai',
      question_count: typed.total,
      question_mix: typed.counts,
      request_id: requestId,
      assessment_style: ADAPTIVE,
    }
  }
  return {
    concept_ids: selected,
    difficulties: bands.slice(0, 1),
    source: 'bank',
    question_count: typed.total,
    question_mix: typed.counts,
    request_id: requestId,
    assessment_style: FIXED,
  }
}

export function isSelectionValid({ style, selected, bands, mix }) {
  const typed = validateFixedMix(mix)
  if (style === FIXED) {
    return selected.length > 0 && bands.length === 1 && typed.valid
  }
  if (style !== ADAPTIVE) return false
  return selected.length === 1 && bands.length === 1 && typed.valid && typed.total >= 3
}
