import { Icon } from './ui'
import { t, useLocale } from '../i18n'

// All questions are selectable in FIXED mode. Every cell exposes its state in
// the accessible name as well as icon/text, so colour is never the only cue.
export default function QuestionPalette({ questions, currentSeq, onJump, disabled }) {
  useLocale()
  const labelFor = (question) => {
    const states = []
    if (question.seq_no === currentSeq) states.push(t('paper.stateCurrent'))
    if (question.answered) states.push(t('paper.stateAnswered'))
    else states.push(t('paper.stateUnanswered'))
    if (question.flagged) states.push(t('paper.stateFlagged'))
    return t('paper.paletteLabel', { number: question.seq_no, state: states.join(', ') })
  }
  const markerFor = (question) => {
    if (question.seq_no === currentSeq) return '●'
    if (question.flagged) return '⚑'
    if (question.answered) return '✓'
    return '–'
  }
  return (
    <section className="question-navigation" aria-label={t('exam.questionList')}>
      <div className="section-heading">
        <h2 className="section-title">
          <Icon name="list" className="icon" />
          {t('exam.questionList')}
        </h2>
        <span className="doing-badge">
          {t('paper.answeredCount', {
            answered: questions.filter((question) => question.answered).length,
            max: questions.length,
            flagged: questions.filter((question) => question.flagged).length,
          })}
        </span>
      </div>
      <div className="navigation-heading">
        <span>{t('exam.questionList')}</span>
        <strong>
          {t('paper.answeredCount', {
            answered: questions.filter((question) => question.answered).length,
            max: questions.length,
            flagged: questions.filter((question) => question.flagged).length,
          })}
        </strong>
      </div>
      <div className="ex-question-grid" role="list" aria-label={t('exam.questionList')}>
        {questions.map((question) => {
          const isCurrent = question.seq_no === currentSeq
          const classes = `question-cell w-full${question.answered ? ' answered' : ''}${isCurrent ? ' active' : ''}${question.flagged ? ' flagged' : ''}`
          return (
            <div key={question.seq_no} role="listitem">
              <button
                type="button"
                className={classes}
                disabled={disabled}
                onClick={() => onJump(question.seq_no)}
                aria-label={labelFor(question)}
                aria-current={isCurrent ? 'step' : undefined}
                title={labelFor(question)}
              >
                <span>{String(question.seq_no).padStart(2, '0')}</span>
                <small>{markerFor(question)}</small>
              </button>
            </div>
          )
        })}
      </div>
      <p className="navigation-note">{t('paper.gridNote')}</p>
    </section>
  )
}
