import { useEffect, useRef, useState } from 'react'
import { i18n, t, typeLabel, validationError, resolveMessage } from '../i18n'
import api, { apiMessage } from '../api'
import { inputCls, btnGhost } from './ui'
import { FormSection } from './admin'

// Conservative inference: code and identifiers alone never establish a language.
export function detectQuestionLanguage(text, fallback = 'en') {
  const prose = text.normalize('NFC').replace(/```[\s\S]*?```|`[^`]*`/g, ' ')
  if (/[ăđơưảạằắẳẵặầấẩẫậẻẹềếểễệỉịỏọồốổỗộờớởỡợủụừứửữựỳỷỹỵ]/i.test(prose)) return 'vi'
  if (/\b(which|what|explain|describe|select the|write a|how does|why does)\b/i.test(prose)) return 'en'
  return fallback
}

export function createQuestionForm() {
  return { question_type: 'mcq', original_locale: i18n.language, language_manual: false, prompt: '', explanation: '', reference_answer: '',
    prompt_translation: '', explanation_translation: '', review_translation: false, translation_open: false,
    tags: [], source_refs: [], difficulty_level: 1, points: '1.0', concept_ids: [], required_concept_ids: [],
    options: ['A', 'B'].map(option_label => ({ option_label, option_text: '', option_translation: '', is_correct: false })),
    datasets: '[]', rubrics: [], translated_rubrics: {},
  }
}

export function questionToForm(d) {
  const original_locale = d.original_locale || 'en'
  const translation = d.translations?.find(row => row.locale === (original_locale === 'en' ? 'vi' : 'en'))
  return { ...createQuestionForm(), ...d, original_locale, language_manual: true,
    concept_ids: d.concepts.filter(c => c.confirmed).map(c => c.concept_id),
    required_concept_ids: d.concepts.filter(c => c.confirmed && c.is_required).map(c => c.concept_id),
    options: (d.options || []).map(o => ({ ...o, option_translation: translation?.option_texts?.[o.option_label] || '' })),
    prompt_translation: translation?.prompt || '', explanation_translation: translation?.explanation || '',
    translation_open: false, translation_current: translation?.current,
    translated_rubrics: translation?.rubrics || {}, rubrics: d.rubrics || [],
    datasets: JSON.stringify(d.datasets || [], null, 2), review_translation: false,
  }
}

export function formToPayload(f) {
  if (!f.prompt.trim()) throw validationError('authoring.promptRequired')
  const payload = { question_type: f.question_type, original_locale: f.original_locale, prompt: f.prompt.trim(),
    explanation: f.explanation?.trim() || null, reference_answer: f.reference_answer || null,
    tags: f.tags, source_refs: f.source_refs, difficulty_level: Number(f.difficulty_level), points: f.points,
    concept_ids: f.concept_ids, required_concept_ids: f.required_concept_ids,
  }
  if (f.question_type === 'mcq') {
    const populated = f.options.filter(o => o.option_text.trim())
    if (populated.length && (populated.length < 2 || populated.length !== f.options.length || populated.filter(o => o.is_correct).length !== 1))
      throw validationError('authoring.optionsRequired')
    payload.options = populated.map(({ option_label, option_text, is_correct }) => ({ option_label, option_text: option_text.trim(), is_correct }))
  }
  if (f.question_type === 'sql') payload.datasets = JSON.parse(f.datasets || '[]')
  if (f.question_type === 'essay') payload.rubrics = f.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({ level_name, min_score, max_score, criteria }))
  if (f.review_translation) {
    if (!f.prompt_translation.trim() || (f.explanation?.trim() && !f.explanation_translation.trim()))
      throw validationError('validation.questionTranslationRequired')
    const translation = { locale: f.original_locale === 'vi' ? 'en' : 'vi', prompt: f.prompt_translation.trim(),
      explanation: f.explanation_translation.trim() || null, option_texts: {}, rubrics: {} }
    if (f.question_type === 'mcq') for (const o of f.options.filter(o => o.option_text.trim())) {
      if (!o.option_translation?.trim()) throw validationError('validation.questionTranslationRequired')
      translation.option_texts[o.option_label] = o.option_translation.trim()
    }
    if (f.question_type === 'essay') for (const r of f.rubrics) {
      const row = f.translated_rubrics[r.level_name]
      if (!row?.label?.trim() || !row?.criteria?.trim()) throw validationError('validation.questionTranslationRequired')
      translation.rubrics[r.level_name] = row
    }
    payload.translations = [translation]
  }
  return payload
}

export function ConceptPicker({ concepts, value, required = [], onChange, onRequired, label }) {
  const [query, setQuery] = useState('')
  const shown = concepts.filter(c => value.includes(c.concept_id) || `${c.concept_name} ${c.concept_code}`.toLowerCase().includes(query.toLowerCase()))
  return <fieldset className="min-w-0 rounded-lg border border-edge p-3">
    <legend className="px-1 text-sm font-medium text-sub">{label || t('common.concepts')}</legend>
    <input aria-label={t('authoring.searchConcepts')} placeholder={t('authoring.searchConcepts')} value={query} onChange={e => setQuery(e.target.value)} className={`${inputCls} mb-3 w-full`} />
    <div className="max-h-64 space-y-2 overflow-auto">
      {!shown.length && <p className="text-sm text-mute">{t('authoring.noConcepts')}</p>}
      {shown.map(c => <div key={c.concept_id} className="flex flex-wrap items-start justify-between gap-2">
        <label className="flex min-w-0 gap-2 text-sm text-sub"><input type="checkbox" checked={value.includes(c.concept_id)} onChange={e => {
          onChange(e.target.checked ? [...value, c.concept_id] : value.filter(id => id !== c.concept_id))
          if (!e.target.checked) onRequired?.(required.filter(id => id !== c.concept_id))
        }} /><span>{c.concept_name} <span className="text-xs text-mute">({c.concept_code})</span></span></label>
        {onRequired && value.includes(c.concept_id) && <label className="flex gap-2 text-xs text-sub"><input type="checkbox" checked={required.includes(c.concept_id)} onChange={e => onRequired(e.target.checked ? [...required, c.concept_id] : required.filter(id => id !== c.concept_id))} />{t('authoring.requiredTechnique')}</label>}
      </div>)}
    </div>
  </fieldset>
}

export function QuestionAuthoring({ form: f, setForm, editing, concepts }) {
  const [preview, setPreview] = useState(false)
  const [previewLocale, setPreviewLocale] = useState('')
  const [translationAvailable, setTranslationAvailable] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [translationNotice, setTranslationNotice] = useState('')
  const [translationError, setTranslationError] = useState('')
  const currentForm = useRef(f)
  currentForm.current = f
  const translationRequest = useRef(null)
  useEffect(() => () => translationRequest.current?.abort(), [])
  useEffect(() => {
    if (!f.translation_open) return
    const controller = new AbortController()
    Promise.resolve(api.get('/admin/question-translation/capability', { signal: controller.signal }))
      .then(r => { if (!controller.signal.aborted) setTranslationAvailable(r?.data?.available === true) })
      .catch(() => { if (!controller.signal.aborted) setTranslationAvailable(false) })
    return () => controller.abort()
  }, [f.translation_open])
  // Compare raw editor state: newer edits may be temporarily invalid. Never
  // invoke input validation from a React state updater or async race guard.
  const draftSignature = form => JSON.stringify(form)
  async function prepareTranslation() {
    setPreparing(true); setTranslationError(''); setTranslationNotice('')
    const controller = new AbortController()
    translationRequest.current = controller
    try {
      const before = draftSignature(f)
      const payload = formToPayload({ ...f, review_translation: false })
      const { data } = await api.post('/admin/question-translation/draft', payload, { signal: controller.signal })
      if (controller.signal.aborted) return
      if (draftSignature(currentForm.current) !== before) { setTranslationNotice('draftSourceChanged'); return }
      const row = data.translation
      setForm(previous => {
        if (draftSignature(previous) !== before) return previous
        return { ...previous, prompt_translation: row.prompt, explanation_translation: row.explanation || '',
          options: previous.options.map(o => ({ ...o, option_translation: row.option_texts?.[o.option_label] || '' })),
          translated_rubrics: row.rubrics || {}, translation_current: undefined,
          translation_dirty: true, review_translation: false }
      })
      setTranslationNotice('draftPrepared')
    } catch (e) {
      if (!controller.signal.aborted) setTranslationError(apiMessage(e))
    } finally {
      if (!controller.signal.aborted) setPreparing(false)
    }
  }
  const set = patch => setForm(previous => {
    const next = { ...previous, ...patch, review_translation: false }
    const translatedText = value => JSON.stringify([value.prompt_translation, value.explanation_translation,
      value.options.map(o => [o.option_label, o.option_translation]), value.translated_rubrics])
    next.translation_dirty = previous.translation_dirty || translatedText(previous) !== translatedText(next)
    const source = value => JSON.stringify([value.question_type, value.original_locale, value.prompt, value.explanation, value.reference_answer,
      value.options.map(o => [o.option_label, o.option_text, o.is_correct]), value.rubrics])
    if (previous.prompt_translation && source(previous) !== source(next)) next.translation_current = false
    return next
  })
  const other = f.original_locale === 'vi' ? 'en' : 'vi'
  const updateOption = (index, patch) => set({ options: f.options.map((o, i) => i === index ? { ...o, ...patch } : o) })
  const updateRubric = (index, patch) => set({ rubrics: f.rubrics.map((r, i) => i === index ? { ...r, ...patch } : r) })
  const language = locale => t(`authoring.${locale}`)
  const translated = previewLocale === other && (f.review_translation || (f.translation_current && !f.translation_dirty))
  const translationStatus = !f.prompt_translation ? 'missingTranslation'
    : f.review_translation ? 'reviewedTranslation'
    : f.translation_current === false ? 'staleTranslation'
    : f.translation_current && !f.translation_dirty ? 'reviewedTranslation' : 'draftTranslation'
  return <>
    <FormSection title={t('admin.questions.sectionBasics')} className="!border-t-0 !pt-0">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-xs text-sub">{t('admin.questions.type')}<select aria-label={t('admin.questions.type')} value={f.question_type} onChange={e => set({ question_type: e.target.value })} className={inputCls}>{['mcq', 'sql', 'essay'].map(kind => <option key={kind} value={kind}>{typeLabel(kind)}</option>)}</select></label>
        <label className="grid gap-1 text-xs text-sub">{t('authoring.originalLanguage')}<select disabled={!!editing} aria-label={t('authoring.originalLanguage')} value={f.original_locale} onChange={e => set({ original_locale: e.target.value, language_manual: true })} className={inputCls}>{['vi', 'en'].map(locale => <option key={locale} value={locale}>{language(locale)}</option>)}</select></label>
      </div>
      <p role="status" className="text-xs text-mute">{t('authoring.detectedLanguage', { language: language(f.original_locale) })} {t('authoring.languageHelp')}</p>
      <label className="grid gap-1 text-xs text-sub">{t('admin.questions.prompt')} · {language(f.original_locale)}<textarea lang={f.original_locale} required aria-label={t('admin.questions.prompt')} value={f.prompt} onChange={e => { const prompt = e.target.value; set({ prompt, ...(!editing && !f.language_manual && !f.prompt_translation ? { original_locale: detectQuestionLanguage(prompt, f.original_locale) } : {}) }) }} rows={3} className={inputCls} /></label>
    </FormSection>
    <FormSection title={t('admin.questions.sectionAnswer')}>
      {f.question_type === 'mcq' && <fieldset className="space-y-3"><legend className="mb-2 text-xs text-sub">{t('admin.questions.options')}</legend>
        {f.options.map((o, i) => <div key={o.option_label} className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-sm text-sub">{o.option_label}</span>
          <input lang={f.original_locale} aria-label={t('admin.questions.optionText', { number: i + 1 })} value={o.option_text} onChange={e => updateOption(i, { option_text: e.target.value })} className={`${inputCls} min-w-0 flex-[1_1_12rem]`} />
          <label className="flex gap-1 text-xs text-sub"><input type="radio" name="correct-answer" checked={o.is_correct} onChange={() => set({ options: f.options.map((option, j) => ({ ...option, is_correct: i === j })) })} />{t('admin.questions.correct')} {o.option_label}</label>
          <button type="button" className={btnGhost} disabled={f.options.length <= 2} aria-label={t('admin.questions.removeOption', { number: o.option_label })} onClick={() => set({ options: f.options.filter((_, j) => i !== j) })}>{t('admin.remove')}</button>
        </div>)}
        <button type="button" className={btnGhost} disabled={f.options.length >= 26} onClick={() => {
          const label = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').find(label => !f.options.some(o => o.option_label === label))
          set({ options: [...f.options, { option_label: label, option_text: '', option_translation: '', is_correct: false }] })
        }}>{t('admin.questions.addOption')}</button>
      </fieldset>}
      {f.question_type !== 'mcq' && <label className="grid gap-1 text-xs text-sub">{t('admin.questions.reference')}<textarea aria-label={t('admin.questions.reference')} value={f.reference_answer || ''} onChange={e => set({ reference_answer: e.target.value })} className={inputCls} rows={3} /></label>}
      <label className="grid gap-1 text-xs text-sub">{t('authoring.explanation')}<textarea lang={f.original_locale} aria-label={t('authoring.explanation')} value={f.explanation || ''} onChange={e => set({ explanation: e.target.value })} className={inputCls} rows={2} /></label>
      {f.question_type === 'sql' && <label className="grid gap-1 text-xs text-sub">{t('admin.questions.datasets')}<p>{t('authoring.datasetHelp')}</p><textarea aria-label={t('admin.questions.datasets')} value={f.datasets} rows={6} onChange={e => set({ datasets: e.target.value })} className={`${inputCls} font-mono`} /></label>}
      {f.question_type === 'essay' && <div className="space-y-3">
        <p className="text-xs text-mute">{t('authoring.rubricHelp')}</p>
        {f.rubrics.map((r, i) => <fieldset key={i} className="space-y-2 rounded-lg border border-edge p-3"><legend className="px-1 text-xs text-sub">{r.level_name}</legend>
          <div className="grid grid-cols-2 gap-2">{['min_score', 'max_score'].map(key => <label key={key} className="grid gap-1 text-xs text-sub">{t(`authoring.${key}`)}<input aria-label={`${r.level_name}: ${t(`authoring.${key}`)}`} type="number" min="0" step="0.01" value={r[key]} onChange={e => updateRubric(i, { [key]: e.target.value })} className={inputCls} /></label>)}</div>
          <textarea lang={f.original_locale} aria-label={`${r.level_name}: ${t('authoring.criteria')}`} value={r.criteria} onChange={e => updateRubric(i, { criteria: e.target.value })} className={`${inputCls} w-full`} />
        </fieldset>)}
        {!f.rubrics.length && <button type="button" className={btnGhost} onClick={() => set({ rubrics: ['Incomplete', 'Partial', 'Mostly Complete', 'Complete'].map(level_name => ({ level_name, min_score: '', max_score: '', criteria: '' })) })}>{t('authoring.addRubric')}</button>}
      </div>}
    </FormSection>
    <FormSection title={t('admin.questions.sectionConcepts')}>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-xs text-sub">{t('common.difficulty')}<select aria-label={t('common.difficulty')} value={f.difficulty_level} onChange={e => set({ difficulty_level: Number(e.target.value) })} className={inputCls}>{[1, 2, 3, 4, 5].map(level => <option key={level} value={level}>{t(`supervisor.${level <= 2 ? 'EASY' : level === 3 ? 'MEDIUM' : 'HARD'}`)} · {level}</option>)}</select></label>
        <label className="grid gap-1 text-xs text-sub">{t('common.points')}<input required aria-label={t('common.points')} type="number" min="0.01" max="999.99" step="0.01" value={f.points} onChange={e => set({ points: e.target.value })} className={inputCls} /></label>
      </div>
      <ConceptPicker concepts={concepts} value={f.concept_ids} required={f.required_concept_ids} onChange={ids => setForm(previous => ({ ...previous, concept_ids: ids }))} onRequired={ids => setForm(previous => ({ ...previous, required_concept_ids: ids }))} />
      <p className="text-xs text-mute">{t('authoring.conceptHelp')}</p>
    </FormSection>
    <details open={f.translation_open} onToggle={e => { const open = e.currentTarget.open; setForm(previous => ({ ...previous, translation_open: open })) }} className="rounded-lg border border-edge p-3">
      <summary className="cursor-pointer text-sm font-medium text-sub">{t('authoring.optionalTranslation')} · {language(other)}</summary>
      <p aria-live="polite" className="mt-2 text-xs text-mute">{t(`authoring.${translationStatus}`)}</p>
      {f.translation_open && <div className="mt-3 space-y-3">
        <p className="text-xs text-mute">{t('authoring.reviewHelp')}</p>
        {translationAvailable && !f.prompt_translation && <button type="button" disabled={preparing} className={btnGhost} onClick={prepareTranslation}>{t(`authoring.${preparing ? 'preparingDraft' : 'prepareDraft'}`)}</button>}
        {!translationAvailable && <p className="text-xs text-mute">{t('authoring.automaticUnavailable')}</p>}
        {translationNotice && <p role="status" className="text-xs text-sub">{t(`authoring.${translationNotice}`)}</p>}
        {translationError && <p role="alert" className="text-xs text-red-300">{resolveMessage(translationError)}</p>}
        {f.translation_current === false && <p role="status" className="text-xs text-amber-300">{t('authoring.staleTranslation')}</p>}
        <label className="grid gap-1 text-xs text-sub">{t('authoring.translatedPrompt')}<textarea lang={other} aria-label={t('authoring.translatedPrompt')} value={f.prompt_translation} rows={3} onChange={e => set({ prompt_translation: e.target.value })} className={inputCls} /></label>
        <label className="grid gap-1 text-xs text-sub">{t('authoring.translatedExplanation')}<textarea lang={other} aria-label={t('authoring.translatedExplanation')} value={f.explanation_translation} onChange={e => set({ explanation_translation: e.target.value })} className={inputCls} /></label>
        {f.question_type === 'mcq' && f.options.map((o, i) => <label key={o.option_label} className="grid gap-1 text-xs text-sub">{t('authoring.translatedOption', { label: o.option_label })}<input lang={other} aria-label={t('authoring.translatedOption', { label: o.option_label })} value={o.option_translation || ''} onChange={e => updateOption(i, { option_translation: e.target.value })} className={inputCls} /></label>)}
        {f.question_type === 'essay' && f.rubrics.map(r => <fieldset key={r.level_name} className="space-y-2"><legend className="text-xs text-sub">{r.level_name}</legend>{['label', 'criteria'].map(key => <label key={key} className="grid gap-1 text-xs text-sub">{t(`authoring.${key}`)}<textarea lang={other} aria-label={`${r.level_name}: ${t('authoring.translated')} ${t(`authoring.${key}`)}`} value={f.translated_rubrics[r.level_name]?.[key] || ''} onChange={e => set({ translated_rubrics: { ...f.translated_rubrics, [r.level_name]: { ...f.translated_rubrics[r.level_name], [key]: e.target.value } } })} className={inputCls} /></label>)}</fieldset>)}
        <label className="flex gap-2 text-sm text-sub"><input type="checkbox" checked={f.review_translation} onChange={e => setForm(previous => ({ ...previous, review_translation: e.target.checked }))} />{t('authoring.reviewed')}</label>
      </div>}
    </details>
    <button type="button" className={`${btnGhost} w-fit`} aria-expanded={preview} onClick={() => setPreview(!preview)}>{t('authoring.preview')}</button>
    {preview && <section aria-label={t('authoring.preview')} className="space-y-3 rounded-lg border border-edge p-4">
      <label className="grid gap-1 text-xs text-sub">{t('authoring.previewLanguage')}<select aria-label={t('authoring.previewLanguage')} className={inputCls} value={previewLocale || f.original_locale} onChange={e => setPreviewLocale(e.target.value)}>{[f.original_locale, other].map(locale => <option key={locale} value={locale}>{language(locale)}</option>)}</select></label>
      <p className="text-xs text-mute">{t('authoring.previewHelp')}</p>
      {previewLocale === other && !translated && <p role="status" className="text-xs text-amber-300">{t('authoring.originalFallback', { language: language(f.original_locale) })}</p>}
      <div lang={translated ? other : f.original_locale} className="space-y-2 whitespace-pre-wrap break-words text-sm text-ink">
        <p>{translated ? f.prompt_translation : f.prompt}</p>
        {f.question_type === 'mcq' && <ul>{f.options.map(o => <li key={o.option_label}>{o.option_label}. {translated ? o.option_translation : o.option_text}{o.is_correct ? ' ✓' : ''}</li>)}</ul>}
        <p>{translated ? f.explanation_translation : f.explanation}</p>
        {f.question_type === 'sql' && <pre className="overflow-auto">{f.reference_answer}</pre>}
        {f.question_type === 'essay' && <ul>{f.rubrics.map(r => <li key={r.level_name}>{translated ? f.translated_rubrics[r.level_name]?.label : r.level_name} ({r.min_score}–{r.max_score}): {translated ? f.translated_rubrics[r.level_name]?.criteria : r.criteria}</li>)}</ul>}
      </div>
    </section>}
  </>
}
