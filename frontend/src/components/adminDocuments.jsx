import { t, useLocale, dateTime, statusLabel } from '../i18n'
import { apiMessage } from '../api'
import { Badge, Card, Icon, btnDanger, btnPrimary } from './ui'
import { ErrorState } from './States'
import { useState } from 'react'

// Presentational pieces for the grounded-document admin screen. They take
// callbacks instead of calling the API so the privacy confirmation, the
// citation advisory and the error states can be verified in isolation.

export function DocumentApprovalForm({ document, busy = false, onApprove }) {
  useLocale()
  const [confirmed, setConfirmed] = useState(false)
  const approve = (event) => {
    event.preventDefault()
    if (confirmed && !busy) onApprove(document.document_id)
  }
  return (
    <form
      onSubmit={approve}
      className="mt-3 rounded-lg border border-amber-400/30 bg-amber-400/[0.06] p-3"
    >
      <p role="note" className="flex items-start gap-2 text-xs text-amber-200">
        <Icon name="shield" className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{t('admin.documents.approvePrivacyWarning')}</span>
      </p>
      <label className="mt-3 flex cursor-pointer items-start gap-2 text-xs font-medium text-ink">
        <input
          type="checkbox"
          required
          checked={confirmed}
          disabled={busy}
          onChange={(event) => setConfirmed(event.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 accent-cyan-400"
        />
        <span>{t('admin.documents.confirmNoPersonalData')}</span>
      </label>
      {!confirmed && (
        <p className="mt-1.5 text-xs text-mute">{t('admin.documents.confirmRequired')}</p>
      )}
      <button type="submit" disabled={!confirmed || busy} className={`${btnPrimary} mt-3 w-full`}>
        {t('admin.documents.approveDocument')}
      </button>
    </form>
  )
}

// The weak-support warning is deliberately advisory: it never disables the
// approve action and never auto-approves. The administrator is the final
// reviewer of whether the quoted text supports the question.
export function CandidateReviewCard({ candidate, busy = false, onApprove, onReject }) {
  useLocale()
  const quote = candidate.quote || candidate.payload?.quote || ''
  const weak = candidate.citation_support === 'weak'
  const canApprove =
    candidate.validation_status === 'validated' &&
    Boolean(candidate.validation_detail?.content_hash) &&
    !candidate.promoted_question_id
  const canReject =
    ['pending', 'validated'].includes(candidate.validation_status) &&
    !candidate.promoted_question_id
  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="teal">{t('admin.documents.detail', { id: candidate.candidate_id })}</Badge>
        {candidate.citation_support === 'ok' ? (
          <Badge tone="green">{t('admin.documents.citationOk')}</Badge>
        ) : weak ? (
          <Badge tone="amber">{t('admin.documents.citationWeak')}</Badge>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <section aria-label={t('admin.documents.question')} className="rounded-lg bg-elev p-3">
          <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-mute">
            {t('admin.documents.question')}
          </h4>
          <p className="whitespace-pre-wrap break-words text-sm text-ink">
            {candidate.payload?.prompt || t('admin.documents.contentUnavailable')}
          </p>
        </section>
        <section aria-label={t('admin.documents.quote')} className="rounded-lg bg-elev p-3">
          <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-mute">
            {t('admin.documents.quote')}
          </h4>
          <blockquote
            data-testid="candidate-quote"
            className="whitespace-pre-wrap break-words border-l-2 border-cyan-400/40 pl-3 text-sm text-sub"
          >
            {quote || t('admin.documents.quoteUnavailable')}
          </blockquote>
        </section>
      </div>

      {weak && (
        <div
          role="note"
          data-testid="citation-weak-warning"
          className="mt-3 flex items-start gap-2 rounded-lg border border-amber-400/30 bg-amber-400/[0.08] p-3 text-xs text-amber-200"
        >
          <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            {candidate.citation_warning}
            {candidate.citation_warning ? ' ' : ''}
            {t('admin.documents.weakWarning')}
          </span>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {canApprove && (
          <button
            type="button"
            disabled={busy}
            onClick={() => onApprove(candidate)}
            className={btnPrimary}
          >
            {t('admin.documents.approve')}
          </button>
        )}
        {canReject && (
          <button
            type="button"
            disabled={busy}
            onClick={() => onReject(candidate)}
            className={btnDanger}
          >
            {t('admin.documents.reject')}
          </button>
        )}
      </div>
    </Card>
  )
}

// Localizes the backend error envelope ({ error: { code, message } }) through
// the shared apiMessage helper so all four generation errors read clearly.
export function GenerationErrorPanel({ error, onRetry }) {
  useLocale()
  if (!error) return null
  return <ErrorState message={apiMessage(error)} onRetry={onRetry} />
}

export function DocumentMeta({ document }) {
  useLocale()
  return (
    <span className="flex flex-wrap items-center gap-1.5">
      <Badge
        tone={
          document.status === 'approved'
            ? 'green'
            : document.status === 'archived'
              ? 'gray'
              : 'amber'
        }
      >
        {statusLabel(document.status)}
      </Badge>
      <span className="text-xs text-mute">
        {t('admin.documents.chunks', { count: document.chunk_count })}
      </span>
      {document.approved_at && (
        <span className="text-xs text-faint">
          {t('admin.documents.approvedAt', { value: dateTime(document.approved_at) })}
        </span>
      )}
    </span>
  )
}
