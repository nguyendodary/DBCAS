// Practice assessment styles. The backend owns the authoritative constraints;
// these helpers keep the browser selection inside them before a start request.
export const FIXED = 'FIXED'
export const ADAPTIVE = 'ADAPTIVE'

// Mirrors PracticeStart.typed_question_limits for the adaptive branch:
// bank-only, one concept, one starting band, MCQ-only, 3..50 questions.
export const ADAPTIVE_MIN_QUESTIONS = 3
export const ADAPTIVE_MAX_QUESTIONS = 50

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

// FREE/FIXED practice keeps the existing self-selected payload: concept,
// difficulty, source and count choices are assembled by the backend and the
// published result is an official percentage score. ADAPTIVE opts into the
// dedicated runner and sends only the fields its validator accepts.
export function buildPracticePayload({ style, selected, bands, source, count, requestId }) {
  const adaptive = style === ADAPTIVE
  const payload = {
    concept_ids: adaptive ? selected.slice(0, 1) : selected,
    difficulties: adaptive ? bands.slice(0, 1) : bands,
    source: adaptive ? 'bank' : source,
    question_count: adaptive ? clampAdaptiveCount(count) : Number(count),
    request_id: requestId,
  }
  if (adaptive) payload.assessment_style = ADAPTIVE
  return payload
}

export function isSelectionValid({ style, selected, bands, source, count, limits }) {
  const parsed = Number(count)
  const countValid = Number.isInteger(parsed) && parsed >= limits.min && parsed <= limits.max
  if (!countValid) return false
  if (style === ADAPTIVE) {
    return selected.length === 1 && bands.length === 1 && source === 'bank'
  }
  return selected.length > 0 && bands.length > 0
}
