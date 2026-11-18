import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  CandidateReviewCard,
  DocumentApprovalForm,
  GenerationErrorPanel,
} from '../components/adminDocuments'
import { apiMessage } from '../api'

const document = { document_id: 7, status: 'draft', title: 'SQL notes' }

const candidate = {
  candidate_id: 42,
  concept_id: 3,
  concept_code: 'SQL-JOIN',
  question_type: 'mcq',
  validation_status: 'validated',
  promoted_question_id: null,
  citation_support: 'weak',
  citation_warning: 'The question text has little overlap with the cited quote.',
  quote: 'WHERE filters rows before grouping.',
  payload: { prompt: 'Which SQL clause chooses the result columns?' },
  validation_detail: { content_hash: 'a'.repeat(64) },
}

const apiError = (code) => ({ response: { data: { error: { code, message: 'server text' } } } })

describe('DocumentApprovalForm', () => {
  it('requires the explicit no-personal-data confirmation before approving', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    render(<DocumentApprovalForm document={document} onApprove={onApprove} />)

    expect(screen.getByRole('note')).toHaveTextContent(/best-effort/i)
    const checkbox = screen.getByRole('checkbox', {
      name: 'I confirm this document contains no personal data.',
    })
    expect(checkbox).toBeRequired()
    const approve = screen.getByRole('button', { name: 'Approve for generation' })
    expect(approve).toBeDisabled()

    await user.click(checkbox)
    expect(approve).toBeEnabled()
    await user.click(approve)
    expect(onApprove).toHaveBeenCalledWith(7)
  })

  it('does not approve when the confirmation is missing', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    render(<DocumentApprovalForm document={document} onApprove={onApprove} />)
    await user.click(screen.getByRole('button', { name: 'Approve for generation' }))
    expect(onApprove).not.toHaveBeenCalled()
  })
})

describe('CandidateReviewCard', () => {
  it('shows the quoted text next to the question', () => {
    render(<CandidateReviewCard candidate={candidate} onApprove={vi.fn()} onReject={vi.fn()} />)
    const question = screen.getByRole('region', { name: 'Question' })
    const quote = screen.getByRole('region', { name: 'Cited quote' })
    expect(question).toHaveTextContent('Which SQL clause chooses the result columns?')
    expect(quote).toHaveTextContent('WHERE filters rows before grouping.')
    expect(screen.getByTestId('candidate-quote')).toHaveTextContent(
      'WHERE filters rows before grouping.',
    )
  })

  it('shows the weak citation warning as advisory without blocking approval', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    render(<CandidateReviewCard candidate={candidate} onApprove={onApprove} onReject={vi.fn()} />)
    const warning = screen.getByTestId('citation-weak-warning')
    expect(warning).toHaveTextContent('The question text has little overlap with the cited quote.')
    expect(warning).toHaveTextContent(/never auto-approves and never blocks approval/i)
    const approve = screen.getByRole('button', { name: 'Approve into bank' })
    expect(approve).toBeEnabled()
    await user.click(approve)
    expect(onApprove).toHaveBeenCalledWith(candidate)
  })

  it('does not show a weak warning when citation support is ok', () => {
    render(
      <CandidateReviewCard
        candidate={{ ...candidate, citation_support: 'ok', citation_warning: null }}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    )
    expect(screen.queryByTestId('citation-weak-warning')).not.toBeInTheDocument()
    expect(screen.getByText('Citation support: ok')).toBeInTheDocument()
  })
})

describe('GenerationErrorPanel', () => {
  it.each([
    ['document_selection_required', 'Select at least one document to generate from.'],
    [
      'too_many_eligible_chunks',
      'The selected documents exceed the per-request chunk limit. Select fewer documents and retry.',
    ],
    ['retrieval_timeout', 'Document retrieval timed out. Select fewer documents and retry.'],
    ['generation_cancelled', 'Generation was cancelled. You can retry with the same selection.'],
  ])('renders a clear message for %s', (code, text) => {
    const error = apiError(code)
    expect(apiMessage(error)).toEqual({ translationKey: `errors.${code}`, values: undefined })
    render(<GenerationErrorPanel error={error} />)
    expect(screen.getByRole('alert')).toHaveTextContent(text)
  })
})
