import { useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { t, useLocale } from '../../i18n'
import { Card } from '../../components/ui'
import { Loading, ErrorState } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'

export default function AdminSystemPage() {
  useLocale()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let canceled = false
    setError(null)
    api
      .get('/admin/system')
      .then((r) => {
        if (!canceled) setData(r.data)
      })
      .catch((e) => {
        if (!canceled) setError(apiMessage(e))
      })
    return () => {
      canceled = true
    }
  }, [retry])
  return (
    <div className="space-y-5">
      <AdminPageHeader title={t('admin.system.title')} subtitle={t('admin.system.subtitle')} />
      {error && <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />}
      {!data ? (
        !error && <Loading />
      ) : (
        <>
          <Card className="space-y-3 p-5">
            <h2 className="text-lg font-semibold">{t('admin.system.workflowTitle')}</h2>
            <p className="text-sub">{t('admin.system.workflowHelp')}</p>
            <ol className="list-decimal space-y-2 pl-5 text-sub">
              <li>
                <strong>{t('admin.system.step1Title')}</strong> {t('admin.system.step1Body')}
              </li>
              <li>
                <strong>{t('admin.system.step2Title')}</strong> {t('admin.system.step2Body')}
              </li>
              <li>
                <strong>{t('admin.system.step3Title')}</strong> {t('admin.system.step3Body')}
              </li>
            </ol>
            <p className="text-sm text-sub">{t('admin.system.note')}</p>
          </Card>
          <Card className="space-y-3 p-5">
            <h2 className="text-lg font-semibold">{t('admin.system.aiTitle')}</h2>
            <p>
              {t('admin.system.promptBuilder')}{' '}
              {data.prompt_builder_configured
                ? t('admin.system.promptModel')
                : t('admin.system.promptTemplate')}
            </p>
            <p>
              {t('admin.system.evaluator')}{' '}
              {data.evaluator_configured
                ? t('admin.system.evaluatorApi')
                : t('admin.system.evaluatorFallback')}
            </p>
            <p className="text-sm text-sub">{t('admin.system.keyNote')}</p>
          </Card>
          <Card className="space-y-2 p-5">
            <h2 className="text-lg font-semibold">{t('admin.system.basicTitle')}</h2>
            <p>{t('admin.system.localRun', { database: data.database })}</p>
            <p>{t('admin.system.pipeline')}</p>
          </Card>
        </>
      )}
    </div>
  )
}
