import { readFileSync } from 'node:fs'

const pack = JSON.parse(
  readFileSync(new URL('../../db/benchmark_pack.json', import.meta.url), 'utf8'),
)
const translations = JSON.parse(
  readFileSync(new URL('../../db/question_translations_vi.json', import.meta.url), 'utf8'),
).questions

// Archived browser data stays unchanged. Newly authored copies use the
// current reviewed answers, fixtures, rubrics, explanations and citations.
export function reviewedBankQuestion(source) {
  const candidates = pack.questions.filter(
    (q) => q.question_type === source.question_type && q.status !== 'retired',
  )
  const current = candidates.find((q) => q.prompt === source.prompt) || candidates[0]
  if (!current) throw new Error('Reviewed source is missing for this question type')
  return {
    ...source,
    ...current,
    concepts: source.concepts,
    options: current.options || [],
    datasets: current.datasets || [],
    rubrics: current.rubrics || [],
    translations: [{ ...translations[current.key], locale: 'vi', current: true }],
  }
}
