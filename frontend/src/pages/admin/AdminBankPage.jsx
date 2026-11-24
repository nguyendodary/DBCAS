import { useSearchParams } from 'react-router-dom'
import AdminQuestionsPage from './AdminQuestionsPage'
import AdminCurriculumPage from './AdminCurriculumPage'
import { btnGhost } from '../../components/ui'
import { t, useLocale } from '../../i18n'
export default function AdminBankPage() {
  useLocale()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'concepts' ? 'concepts' : 'questions'
  return (
    <div className="space-y-5">
      <nav aria-label={t('ui.bank.aria')} className="flex flex-wrap gap-3">
        <button
          type="button"
          className={btnGhost}
          aria-pressed={tab === 'questions'}
          onClick={() => setParams({})}
        >
          {t('ui.bank.questions')}
        </button>
        <button
          type="button"
          className={btnGhost}
          aria-pressed={tab === 'concepts'}
          onClick={() => setParams({ tab: 'concepts' })}
        >
          {t('ui.bank.concepts')}
        </button>
      </nav>
      {tab === 'concepts' ? <AdminCurriculumPage /> : <AdminQuestionsPage />}
    </div>
  )
}
