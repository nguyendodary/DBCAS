import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import { i18n, setLocale } from '../i18n'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'
import { QuestionAuthoring, createQuestionForm, formToPayload, questionToForm, detectQuestionLanguage } from '../components/QuestionAuthoring'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn(), put: vi.fn() }, apiMessage: e => e.message }))
const concept = { concept_id: 9, concept_code: 'FILTER', concept_name: 'Filtering rows', confirmed: true }
beforeEach(async () => {
  vi.resetAllMocks()
  await i18n.changeLanguage('en')
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? [concept] : [] }))
  api.post.mockResolvedValue({ data: {} })
  api.put.mockResolvedValue({ data: {} })
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
})
afterEach(async () => { await act(() => i18n.changeLanguage('en')); vi.restoreAllMocks() })

function enableTranslation(response) {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? [concept] : url.endsWith('/capability') ? { available: true } : [] }))
  api.post.mockImplementation(url => url.endsWith('/question-translation/draft') ? response() : Promise.resolve({ data: {} }))
}

const machineDraft = { data: { status: 'draft', translation: { locale: 'en', prompt: 'Which clause filters rows?',
  option_texts: { A: 'WHERE', B: 'ORDER BY' }, rubrics: {} } } }

it.each([false, true])('machine drafts require explicit human review before saving: review=%s', async reviewed => {
  enableTranslation(() => Promise.resolve(machineDraft))
  await authored('vi')
  await userEvent.click(screen.getByText(/Optional reviewed translation/))
  await userEvent.click(await screen.findByRole('button', { name: 'Prepare translation draft' }))
  await waitFor(() => expect(screen.getByLabelText('Translated question prompt')).toHaveValue('Which clause filters rows?'))
  const review = screen.getByLabelText('I reviewed this translation against the current original and grading criteria.')
  expect(review).not.toBeChecked()
  if (reviewed) await userEvent.click(review)
  await userEvent.click(screen.getByRole('button', { name: 'Save draft', exact: true }))
  const saved = api.post.mock.calls.find(([url]) => url === '/admin/questions')[1]
  if (reviewed) expect(saved.translations[0].locale).toBe('en')
  else expect(saved).not.toHaveProperty('translations')
  expect(saved.options.find(o => o.is_correct).option_label).toBe('A')
})

it.each(['prompt', 'incomplete option'])('keeps newer %s edits when an in-flight draft finishes without blocking original saving', async changed => {
  let finish
  enableTranslation(() => new Promise(resolve => { finish = resolve }))
  await authored('vi')
  await userEvent.click(screen.getByText(/Optional reviewed translation/))
  await userEvent.click(await screen.findByRole('button', { name: 'Prepare translation draft' }))
  expect(screen.getByRole('button', { name: 'Save draft', exact: true })).toBeEnabled()
  if (changed === 'prompt') fireEvent.change(screen.getByLabelText('Question prompt'), { target: { value: 'Nội dung mới SELECT.' } })
  else fireEvent.change(screen.getByLabelText('Option 1 text'), { target: { value: '' } })
  await act(async () => finish(machineDraft))
  expect(screen.getByLabelText('Translated question prompt')).toHaveValue('')
  expect(screen.getByText(/newer edits were kept/)).toBeInTheDocument()
})

it('keeps manual translation and original saving available after a provider failure', async () => {
  enableTranslation(() => Promise.reject(new Error('Provider unavailable')))
  await authored('vi')
  await userEvent.click(screen.getByText(/Optional reviewed translation/))
  await userEvent.click(await screen.findByRole('button', { name: 'Prepare translation draft' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Provider unavailable')
  expect(screen.getByLabelText('Translated question prompt')).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Save draft', exact: true })).toBeEnabled()
})

async function authored(locale) {
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  await userEvent.selectOptions(screen.getByLabelText('Question content language'), locale)
  fireEvent.change(screen.getByLabelText('Question prompt'), { target: { value: locale === 'vi' ? 'Mệnh đề nào lọc dòng?' : 'Which clause filters rows?' } })
  fireEvent.change(screen.getByLabelText('Option 1 text'), { target: { value: 'WHERE' } })
  fireEvent.change(screen.getByLabelText('Option 2 text'), { target: { value: 'ORDER BY' } })
  await userEvent.click(screen.getByRole('radio', { name: 'correct A' }))
  await userEvent.click(await screen.findByRole('checkbox', { name: 'Filtering rows (FILTER)' }))
}

it.each(['en', 'vi'])('creates a %s original without a translation', async locale => {
  await authored(locale)
  expect(screen.queryByLabelText('Translated question prompt')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save draft', exact: true }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions', expect.objectContaining({ original_locale: locale, concept_ids: [9] })))
  expect(api.post.mock.calls[0][1]).not.toHaveProperty('translations')
})

it('requires review for optional translation and keeps answer labels stable', async () => {
  await authored('vi')
  await userEvent.click(screen.getByText(/Optional reviewed translation/))
  fireEvent.change(await screen.findByLabelText('Translated question prompt'), { target: { value: 'Which clause filters rows?' } })
  fireEvent.change(screen.getByLabelText('Translated option A'), { target: { value: 'WHERE' } })
  fireEvent.change(screen.getByLabelText('Translated option B'), { target: { value: 'ORDER BY' } })
  await userEvent.click(screen.getByLabelText('I reviewed this translation against the current original and grading criteria.'))
  await userEvent.click(screen.getByRole('button', { name: 'Preview question' }))
  await userEvent.selectOptions(screen.getByLabelText('Preview content language'), 'en')
  expect(screen.getByText('Which clause filters rows?', { selector: 'p' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save draft', exact: true }))
  await waitFor(() => expect(api.post).toHaveBeenCalled())
  const payload = api.post.mock.calls[0][1]
  expect(payload.translations).toEqual([{ locale: 'en', prompt: 'Which clause filters rows?', explanation: null, option_texts: { A: 'WHERE', B: 'ORDER BY' }, rubrics: {} }])
  expect(payload.options.filter(o => o.is_correct).map(o => o.option_label)).toEqual(['A'])
})

it('clears translation review when source changes and previews the original fallback', async () => {
  await authored('en')
  await userEvent.click(screen.getByText(/Optional reviewed translation/))
  const reviewed = await screen.findByLabelText('I reviewed this translation against the current original and grading criteria.')
  await userEvent.click(reviewed)
  await userEvent.type(screen.getByLabelText('Question prompt'), ' Revised')
  expect(reviewed).not.toBeChecked()
  await userEvent.click(screen.getByRole('button', { name: 'Preview question' }))
  await userEvent.selectOptions(screen.getByLabelText('Preview content language'), 'vi')
  expect(screen.getByText('No reviewed translation for this preview. Showing the English original.')).toBeInTheDocument()
})

it('keeps UI language independent from the authored language and option text', async () => {
  await authored('vi')
  await act(() => setLocale('vi'))
  expect(screen.getByLabelText('Ngôn ngữ nội dung câu hỏi')).toHaveValue('vi')
  expect(screen.getByLabelText('Nội dung lựa chọn 1')).toHaveValue('WHERE')
  expect(screen.getByLabelText('Nội dung câu hỏi')).toHaveValue('Mệnh đề nào lọc dòng?')
})

it('does not invent option labels after removal and addition', async () => {
  await authored('en')
  await userEvent.click(screen.getByRole('button', { name: '+ add option' }))
  await userEvent.click(screen.getByRole('button', { name: 'Remove option B' }))
  await userEvent.click(screen.getByRole('button', { name: '+ add option' }))
  expect(screen.getAllByRole('radio').map(r => r.closest('label').textContent)).toEqual(['correct A', 'correct C', 'correct B'])
})

it('uses structured essay criteria and preserves SQL identifiers', () => {
  const f = createQuestionForm()
  Object.assign(f, { original_locale: 'vi', question_type: 'sql', prompt: 'Liệt kê students.id', reference_answer: 'SELECT id FROM students', datasets: '[{"dataset_name":"base","setup_sql":"CREATE TABLE students(id int)","expected_result":{"rows":[]}}]' })
  expect(formToPayload(f).reference_answer).toBe('SELECT id FROM students')
  const rubric = [{ level_name: 'Complete', min_score: '4', max_score: '5', criteria: 'Giải thích đầy đủ' }]
  Object.assign(f, { question_type: 'essay', rubrics: rubric })
  expect(formToPayload(f).rubrics).toEqual(rubric)
})

it('loads existing translations without silently reapproving them', () => {
  const f = questionToForm({ question_type: 'mcq', prompt: 'Original', concepts: [concept], options: [{ option_label: 'A', option_text: 'WHERE', is_correct: true }, { option_label: 'B', option_text: 'ORDER BY', is_correct: false }], translations: [{ locale: 'vi', prompt: 'Bản dịch cũ', current: false, option_texts: { A: 'WHERE', B: 'ORDER BY' } }] })
  expect(f.original_locale).toBe('en')
  expect(f.prompt_translation).toBe('Bản dịch cũ')
  expect(f.review_translation).toBe(false)
  expect(formToPayload(f)).not.toHaveProperty('translations')
})

it.each([
  ['Chon menh de loc dong', 'vi', 'vi'],
  ['Chon menh de loc dong', 'en', 'en'],
  ['Which clause lọc rows?', 'en', 'vi'],
  ['SELECT id FROM students WHERE id > 1', 'vi', 'vi'],
  ['SQL', 'en', 'en'],
  ['JOIN', 'vi', 'vi'],
  ['?', 'vi', 'vi'],
  ['Explain `địa_chỉ` in this query', 'vi', 'en'],
])('handles ambiguous/mixed prose %s with a correctable fallback', (prompt, fallback, expected) => {
  expect(detectQuestionLanguage(prompt, fallback)).toBe(expected)
})

it('lets an administrator correct ambiguous detection and keeps that correction while typing', async () => {
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  fireEvent.change(screen.getByLabelText('Question prompt'), { target: { value: 'Chon menh de loc dong' } })
  await userEvent.selectOptions(screen.getByLabelText('Question content language'), 'vi')
  fireEvent.change(screen.getByLabelText('Question prompt'), { target: { value: 'Which SQL query? Chon cau lenh.' } })
  expect(screen.getByLabelText('Question content language')).toHaveValue('vi')
})

it('offers a structured four-band essay editor without choosing score boundaries', async () => {
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  await userEvent.selectOptions(screen.getByLabelText('Question type'), 'essay')
  await userEvent.click(screen.getByRole('button', { name: 'Add four grading bands' }))
  expect(screen.getByLabelText('Complete: Minimum score')).toHaveValue(null)
  fireEvent.change(screen.getByLabelText('Complete: Criteria'), { target: { value: 'Explain normalization' } })
  expect(screen.getByLabelText('Complete: Criteria')).toHaveValue('Explain normalization')
})


it('infers prose language conservatively without treating SQL identifiers as English', () => {
  expect(detectQuestionLanguage('Mệnh đề nào lọc dòng?', 'en')).toBe('vi')
  expect(detectQuestionLanguage('Which clause filters rows?', 'vi')).toBe('en')
  expect(detectQuestionLanguage('SELECT id FROM students', 'vi')).toBe('vi')
  expect(detectQuestionLanguage('`đơn_vị`', 'en')).toBe('en')
  expect(detectQuestionLanguage('Mệnh đề nào lọc dòng?'.normalize('NFD'), 'en')).toBe('vi')
  expect(detectQuestionLanguage('Which café table is indexed?', 'vi')).toBe('en')
})

it('previews a stored reviewed translation without requiring or resubmitting another approval', async () => {
  const form = questionToForm({ question_type: 'mcq', prompt: 'Original question', concepts: [],
    options: [{ option_label: 'A', option_text: 'WHERE', is_correct: true }, { option_label: 'B', option_text: 'ORDER BY', is_correct: false }],
    translations: [{ locale: 'vi', prompt: 'Mệnh đề nào lọc dòng?', current: true, option_texts: { A: 'WHERE', B: 'ORDER BY' } }],
  })
  const setForm = vi.fn()
  render(<QuestionAuthoring form={form} setForm={setForm} editing concepts={[]} />)
  await userEvent.click(screen.getByRole('button', { name: 'Preview question' }))
  await userEvent.selectOptions(screen.getByLabelText('Preview content language'), 'vi')
  expect(screen.getByText('Mệnh đề nào lọc dòng?', { selector: 'p' })).toBeInTheDocument()
  expect(formToPayload(form)).not.toHaveProperty('translations')
  await userEvent.selectOptions(screen.getByLabelText('Question type'), 'essay')
  const changedType = setForm.mock.calls.at(-1)[0](form)
  expect(changedType.translation_current).toBe(false)
  expect(changedType.review_translation).toBe(false)
})

it.each([['vi', 'Mệnh đề nào lọc dòng?'], ['en', 'Which clause filters rows?']])('authors %s without selecting a source language', async (locale, prompt) => {
  await i18n.changeLanguage(locale === 'vi' ? 'en' : 'vi')
  const { t } = await import('../i18n')
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: t('admin.questions.new') }))
  fireEvent.change(screen.getByLabelText(t('admin.questions.prompt')), { target: { value: prompt } })
  expect(screen.getByLabelText(t('authoring.originalLanguage'))).toHaveValue(locale)
})
