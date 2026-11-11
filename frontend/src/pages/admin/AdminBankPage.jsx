import { useSearchParams } from 'react-router-dom'
import AdminQuestionsPage from './AdminQuestionsPage'
import AdminCurriculumPage from './AdminCurriculumPage'
import { btnGhost } from '../../components/ui'
export default function AdminBankPage() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'concepts' ? 'concepts' : 'questions'
  return (
    <div className="space-y-5">
      <nav aria-label="Ngân hàng câu hỏi và khái niệm" className="flex flex-wrap gap-3">
        <button
          type="button"
          className={btnGhost}
          aria-pressed={tab === 'questions'}
          onClick={() => setParams({})}
        >
          Câu hỏi
        </button>
        <button
          type="button"
          className={btnGhost}
          aria-pressed={tab === 'concepts'}
          onClick={() => setParams({ tab: 'concepts' })}
        >
          Khái niệm & CLO
        </button>
      </nav>
      {tab === 'concepts' ? <AdminCurriculumPage /> : <AdminQuestionsPage />}
    </div>
  )
}
