import { useState } from 'react'
import { t, typeLabel, validationError } from '../i18n'
import { inputCls, btnGhost } from './ui'
import { FormSection } from './admin'

// Conservative inference: code and identifiers alone never establish a language.
export function detectQuestionLanguage(text, fallback = 'en') {
  const prose = text.normalize('NFC').replace(/```[\s\S]*?```|`[^`]*`/g, ' ')
  if (/[ăđơưảạằắẳẵặầấẩẫậẻẹềếểễệỉịỏọồốổỗộờớởỡợủụừứửữựỳỷỹỵ]/i.test(prose)) return 'vi'
  if (/\b(which|what|explain|describe|select the|write a|how does|why does)\b/i.test(prose))
    return 'en'
  return fallback
}

export function createQuestionForm() {
  return {
    question_type: 'mcq',
    original_locale: 'en',
    prompt: '',
    explanation: '',
    reference_answer: '',
    prompt_translation: '',
    explanation_translation: '',
    review_translation: false,
    tags: [],
    source_refs: [],
    difficulty_level: 1,
    points: '1.0',
    concept_ids: [],
    required_concept_ids: [],
    options: ['A', 'B', 'C', 'D'].map((option_label) => ({
      option_label,
      option_text: '',
      option_translation: '',
      is_correct: false,
    })),
    datasets: '[]',
    rubrics: [],
    translated_rubrics: {},
  }
}

export function questionToForm(d) {
  const original_locale = d.original_locale || 'en'
  const translation = d.translations?.find(
    (row) => row.locale === (original_locale === 'en' ? 'vi' : 'en'),
  )
  return {
    ...createQuestionForm(),
    ...d,
    original_locale,
    concept_ids: d.concepts.filter((c) => c.confirmed).map((c) => c.concept_id),
    required_concept_ids: d.concepts
      .filter((c) => c.confirmed && c.is_required)
      .map((c) => c.concept_id),
    options: (d.options || []).map((o) => ({
      ...o,
      option_translation: translation?.option_texts?.[o.option_label] || '',
    })),
    prompt_translation: translation?.prompt || '',
    explanation_translation: translation?.explanation || '',
    translation_current: translation?.current,
    translated_rubrics: translation?.rubrics || {},
    rubrics: d.rubrics || [],
    datasets: JSON.stringify(d.datasets || [], null, 2),
    review_translation: false,
  }
}

export function formToPayload(f) {
  if (!f.prompt.trim()) throw validationError('authoring.promptRequired')
  const payload = {
    question_type: f.question_type,
    original_locale: f.original_locale,
    prompt: f.prompt.trim(),
    explanation: f.explanation?.trim() || null,
    reference_answer: f.reference_answer || null,
    tags: f.tags,
    source_refs: f.source_refs,
    difficulty_level: Number(f.difficulty_level),
    points: f.points,
    concept_ids: f.concept_ids,
    required_concept_ids: f.required_concept_ids,
  }
  if (f.source_urls !== undefined)
    payload.source_refs = [
      ...new Set(
        f.source_urls
          .split(/\r?\n/)
          .map((url) => url.trim())
          .filter(Boolean),
      ),
    ].map((url) => f.source_refs.find((ref) => ref.url === url) || { url, version: '18' })
  if (f.question_type === 'mcq') {
    const populated = f.options.filter((o) => o.option_text.trim())
    if (
      populated.length &&
      (populated.length < 2 ||
        populated.length !== f.options.length ||
        populated.filter((o) => o.is_correct).length !== 1)
    )
      throw validationError('authoring.optionsRequired')
    payload.options = populated.map(({ option_label, option_text, is_correct }) => ({
      option_label,
      option_text: option_text.trim(),
      is_correct,
    }))
  }
  if (f.question_type === 'sql') payload.datasets = JSON.parse(f.datasets || '[]')
  if (f.question_type === 'essay')
    payload.rubrics = f.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({
      level_name,
      min_score,
      max_score,
      criteria,
    }))
  if (f.review_translation) {
    if (
      !f.prompt_translation.trim() ||
      (f.explanation?.trim() && !f.explanation_translation.trim())
    )
      throw validationError('validation.questionTranslationRequired')
    const translation = {
      locale: f.original_locale === 'vi' ? 'en' : 'vi',
      prompt: f.prompt_translation.trim(),
      explanation: f.explanation_translation.trim() || null,
      option_texts: {},
      rubrics: {},
    }
    if (f.question_type === 'mcq')
      for (const o of f.options.filter((o) => o.option_text.trim())) {
        if (!o.option_translation?.trim())
          throw validationError('validation.questionTranslationRequired')
        translation.option_texts[o.option_label] = o.option_translation.trim()
      }
    if (f.question_type === 'essay')
      for (const r of f.rubrics) {
        const row = f.translated_rubrics[r.level_name]
        if (!row?.label?.trim() || !row?.criteria?.trim())
          throw validationError('validation.questionTranslationRequired')
        translation.rubrics[r.level_name] = row
      }
    payload.translations = [translation]
  }
  return payload
}

export function ConceptPicker({ concepts, value, required = [], onChange, onRequired, label }) {
  const [query, setQuery] = useState('')
  const shown = concepts.filter(
    (c) =>
      value.includes(c.concept_id) ||
      `${c.concept_name} ${c.concept_code}`.toLowerCase().includes(query.toLowerCase()),
  )
  return (
    <fieldset className="min-w-0 rounded-lg border border-edge p-3">
      <legend className="px-1 text-sm font-medium text-sub">{label || t('common.concepts')}</legend>
      <input
        aria-label={t('authoring.searchConcepts')}
        placeholder={t('authoring.searchConcepts')}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className={`${inputCls} mb-3 w-full`}
      />
      <div className="max-h-64 space-y-2 overflow-auto">
        {!shown.length && <p className="text-sm text-mute">{t('authoring.noConcepts')}</p>}
        {shown.map((c) => (
          <div key={c.concept_id} className="flex flex-wrap items-start justify-between gap-2">
            <label className="flex min-w-0 gap-2 text-sm text-sub">
              <input
                type="checkbox"
                checked={value.includes(c.concept_id)}
                onChange={(e) => {
                  onChange(
                    e.target.checked
                      ? [...value, c.concept_id]
                      : value.filter((id) => id !== c.concept_id),
                  )
                  if (!e.target.checked) onRequired?.(required.filter((id) => id !== c.concept_id))
                }}
              />
              <span>
                {c.concept_name} <span className="text-xs text-mute">({c.concept_code})</span>
              </span>
            </label>
            {onRequired && value.includes(c.concept_id) && (
              <label className="flex gap-2 text-xs text-sub">
                <input
                  type="checkbox"
                  checked={required.includes(c.concept_id)}
                  onChange={(e) =>
                    onRequired(
                      e.target.checked
                        ? [...required, c.concept_id]
                        : required.filter((id) => id !== c.concept_id),
                    )
                  }
                />
                {t('authoring.requiredTechnique')}
              </label>
            )}
          </div>
        ))}
      </div>
    </fieldset>
  )
}

export function QuestionAuthoring({ form: f, setForm, editing, concepts }) {
  const [preview, setPreview] = useState(false)
  const set = (patch) =>
    setForm((previous) => {
      const next = { ...previous, ...patch }
      const source = (value) =>
        JSON.stringify([
          value.question_type,
          value.original_locale,
          value.prompt,
          value.explanation,
          value.reference_answer,
          value.options.map((o) => [o.option_label, o.option_text, o.is_correct]),
          value.rubrics,
        ])
      if (previous.prompt_translation && source(previous) !== source(next))
        next.translation_current = false
      return next
    })
  const updateOption = (index, patch) =>
    set({ options: f.options.map((o, i) => (i === index ? { ...o, ...patch } : o)) })
  const updateRubric = (index, patch) =>
    set({ rubrics: f.rubrics.map((r, i) => (i === index ? { ...r, ...patch } : r)) })
  return (
    <>
      <FormSection title={t('admin.questions.sectionBasics')} className="!border-t-0 !pt-0">
        <div className="grid gap-3">
          <label className="grid gap-1 text-xs text-sub">
            {t('admin.questions.type')}
            <select
              aria-label={t('admin.questions.type')}
              value={f.question_type}
              onChange={(e) => set({ question_type: e.target.value })}
              className={inputCls}
            >
              {['mcq', 'sql', 'essay'].map((kind) => (
                <option key={kind} value={kind}>
                  {typeLabel(kind)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="grid gap-1 text-xs text-sub">
          {t('admin.questions.prompt')}
          <textarea
            lang={f.original_locale}
            required
            aria-label={t('admin.questions.prompt')}
            value={f.prompt}
            onChange={(e) => {
              const prompt = e.target.value
              set({
                prompt,
                ...(!editing
                  ? { original_locale: detectQuestionLanguage(prompt, 'en') }
                  : {}),
              })
            }}
            rows={3}
            className={inputCls}
          />
        </label>
      </FormSection>
      <FormSection title={t('admin.questions.sectionAnswer')}>
        {f.question_type === 'mcq' && (
          <fieldset className="space-y-3">
            <legend className="mb-2 text-xs text-sub">{t('admin.questions.options')}</legend>
            {f.options.map((o, i) => (
              <div key={o.option_label} className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-sub">{o.option_label}</span>
                <input
                  lang={f.original_locale}
                  aria-label={t('admin.questions.optionText', { number: i + 1 })}
                  value={o.option_text}
                  onChange={(e) => updateOption(i, { option_text: e.target.value })}
                  className={`${inputCls} min-w-0 flex-[1_1_12rem]`}
                />
                <label className="flex gap-1 text-xs text-sub">
                  <input
                    type="radio"
                    name="correct-answer"
                    checked={o.is_correct}
                    onChange={() =>
                      set({
                        options: f.options.map((option, j) => ({ ...option, is_correct: i === j })),
                      })
                    }
                  />
                  {t('admin.questions.correct')} {o.option_label}
                </label>
                <button
                  type="button"
                  className={btnGhost}
                  disabled={f.options.length <= 2}
                  aria-label={t('admin.questions.removeOption', { number: o.option_label })}
                  onClick={() => set({ options: f.options.filter((_, j) => i !== j) })}
                >
                  {t('admin.remove')}
                </button>
              </div>
            ))}
            <button
              type="button"
              className={btnGhost}
              disabled={f.options.length >= 4}
              onClick={() => {
                const label = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  .split('')
                  .find((label) => !f.options.some((o) => o.option_label === label))
                set({
                  options: [
                    ...f.options,
                    {
                      option_label: label,
                      option_text: '',
                      option_translation: '',
                      is_correct: false,
                    },
                  ],
                })
              }}
            >
              {t('admin.questions.addOption')}
            </button>
          </fieldset>
        )}
        {f.question_type !== 'mcq' && (
          <label className="grid gap-1 text-xs text-sub">
            {t('admin.questions.reference')}
            <textarea
              aria-label={t('admin.questions.reference')}
              value={f.reference_answer || ''}
              onChange={(e) => set({ reference_answer: e.target.value })}
              className={inputCls}
              rows={3}
            />
          </label>
        )}
        <label className="grid gap-1 text-xs text-sub">
          {t('authoring.explanation')}
          <textarea
            lang={f.original_locale}
            aria-label={t('authoring.explanation')}
            value={f.explanation || ''}
            onChange={(e) => set({ explanation: e.target.value })}
            className={inputCls}
            rows={2}
          />
        </label>
        <label className="grid gap-1 text-xs text-sub">
          {t('authoring.sources')}
          <textarea
            aria-label={t('authoring.sources')}
            value={f.source_urls ?? (f.source_refs || []).map((ref) => ref.url).join('\n')}
            onChange={(e) => set({ source_urls: e.target.value })}
            className={inputCls}
            rows={2}
            placeholder="https://www.postgresql.org/docs/18/queries-select-lists.html"
          />
        </label>
        <p className="text-xs text-mute">{t('authoring.sourcesHelp')}</p>
        {f.question_type === 'sql' && (
          <label className="grid gap-1 text-xs text-sub">
            {t('admin.questions.datasets')}
            <p>{t('authoring.datasetHelp')}</p>
            <textarea
              aria-label={t('admin.questions.datasets')}
              value={f.datasets}
              rows={6}
              onChange={(e) => set({ datasets: e.target.value })}
              className={`${inputCls} font-mono`}
            />
          </label>
        )}
        {f.question_type === 'essay' && (
          <div className="space-y-3">
            <p className="text-xs text-mute">{t('authoring.rubricHelp')}</p>
            {f.rubrics.map((r, i) => (
              <fieldset key={i} className="space-y-2 rounded-lg border border-edge p-3">
                <legend className="px-1 text-xs text-sub">{r.level_name}</legend>
                <div className="grid grid-cols-2 gap-2">
                  {['min_score', 'max_score'].map((key) => (
                    <label key={key} className="grid gap-1 text-xs text-sub">
                      {t(`authoring.${key}`)}
                      <input
                        aria-label={`${r.level_name}: ${t(`authoring.${key}`)}`}
                        type="number"
                        min="0"
                        step="0.01"
                        value={r[key]}
                        onChange={(e) => updateRubric(i, { [key]: e.target.value })}
                        className={inputCls}
                      />
                    </label>
                  ))}
                </div>
                <textarea
                  lang={f.original_locale}
                  aria-label={`${r.level_name}: ${t('authoring.criteria')}`}
                  value={r.criteria}
                  onChange={(e) => updateRubric(i, { criteria: e.target.value })}
                  className={`${inputCls} w-full`}
                />
              </fieldset>
            ))}
            {!f.rubrics.length && (
              <button
                type="button"
                className={btnGhost}
                onClick={() =>
                  set({
                    rubrics: ['Incomplete', 'Partial', 'Mostly Complete', 'Complete'].map(
                      (level_name) => ({ level_name, min_score: '', max_score: '', criteria: '' }),
                    ),
                  })
                }
              >
                {t('authoring.addRubric')}
              </button>
            )}
          </div>
        )}
      </FormSection>
      <FormSection title={t('admin.questions.sectionConcepts')}>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-1 text-xs text-sub">
            {t('common.difficulty')}
            <select
              aria-label={t('common.difficulty')}
              value={f.difficulty_level}
              onChange={(e) => set({ difficulty_level: Number(e.target.value) })}
              className={inputCls}
            >
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={level}>
                  {t(`supervisor.${level <= 2 ? 'EASY' : level === 3 ? 'MEDIUM' : 'HARD'}`)} ·{' '}
                  {level}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-xs text-sub">
            {t('common.points')}
            <input
              required
              aria-label={t('common.points')}
              type="number"
              min="0.01"
              max="999.99"
              step="0.01"
              value={f.points}
              onChange={(e) => set({ points: e.target.value })}
              className={inputCls}
            />
          </label>
        </div>
        <ConceptPicker
          concepts={concepts}
          value={f.concept_ids}
          required={f.required_concept_ids}
          onChange={(ids) => setForm((previous) => ({ ...previous, concept_ids: ids }))}
          onRequired={(ids) => setForm((previous) => ({ ...previous, required_concept_ids: ids }))}
        />
        <p className="text-xs text-mute">{t('authoring.conceptHelp')}</p>
      </FormSection>
      <button
        type="button"
        className={`${btnGhost} w-fit`}
        aria-expanded={preview}
        onClick={() => setPreview(!preview)}
      >
        {t('authoring.preview')}
      </button>
      {preview && (
        <section
          aria-label={t('authoring.preview')}
          className="space-y-3 rounded-lg border border-edge p-4"
        >
          <p className="text-xs text-mute">{t('authoring.previewHelp')}</p>
          <div
            lang={f.original_locale}
            className="space-y-2 whitespace-pre-wrap break-words text-sm text-ink"
          >
            <div className="rounded-lg border border-edge2 bg-surface px-4 py-3">
              <p className="mb-1 text-xs font-medium text-mute">
                {t('admin.questions.prompt')}
              </p>
              <p className="font-medium leading-relaxed">{f.prompt || '…'}</p>
            </div>
            {f.question_type === 'mcq' && (
              <ul className="space-y-2">
                {f.options.map((o) => (
                  <li
                    key={o.option_label}
                    className="flex items-center gap-3 rounded-lg border border-edge px-3 py-2"
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-edge2 text-xs font-semibold">
                      {o.option_label}
                    </span>
                    <span className="min-w-0 flex-1">{o.option_text || '…'}</span>
                    {o.is_correct && <span className="text-xs font-medium text-cyan-300">✓</span>}
                  </li>
                ))}
              </ul>
            )}
            {f.explanation && <p>{f.explanation}</p>}
            {f.question_type === 'sql' && <pre className="overflow-auto">{f.reference_answer}</pre>}
            {f.question_type === 'essay' && (
              <ul>
                {f.rubrics.map((r) => (
                  <li key={r.level_name}>
                    {r.level_name} ({r.min_score}–{r.max_score}): {r.criteria}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}
    </>
  )
}
