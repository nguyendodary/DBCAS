import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Card, Notice, PageHeader, Pagination, StatusBadge, inputCls } from '../../components/ui'

// UC04 — provision accounts (start disabled) and activate verified ones.
export default function AdminAccountsPage() {
  useLocale()
  const [accounts, setAccounts] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'Administrator' })
  const [busy, setBusy] = useState(false)
  const [page, setPage] = useState(1)

  const load = useCallback(() => {
    setError('')
    api
      .get('/admin/accounts')
      .then((r) => setAccounts(r.data))
      .catch((e) => {
        setError(apiMessage(e))
        setAccounts([])
      })
  }, [])

  useEffect(load, [load])

  async function provision(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/admin/accounts', form)
      setNotice(message('admin.accounts.provisioned', { email: form.email }))
      setForm({ name: '', email: '', password: '', role: 'Administrator' })
      load()
    } catch (e2) {
      setError(apiMessage(e2))
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(account, status) {
    setError('')
    try {
      await api.patch(`/admin/accounts/${account.account_id}`, { status })
      load()
    } catch (e) {
      setError(apiMessage(e))
    }
  }

  const pageCount = Math.ceil((accounts?.length || 0) / 10)
  const currentPage = Math.min(page, pageCount || 1)

  return (
    <div className="space-y-4">
      <PageHeader
        title={t('admin.accounts.title')}
        subtitle={
          t('admin.accounts.intro')
        }
      />

      <Card className="p-4 sm:p-5">
        <h2 className="mb-3 text-sm font-semibold text-ink">{t('admin.accounts.provisionTitle')}</h2>
        <form onSubmit={provision} className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
          <input
            aria-label={t('common.fullName')}
            required
            placeholder={t('common.fullName')}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className={inputCls}
          />
          <input
            aria-label={t('admin.accounts.email')}
            required
            type="email"
            placeholder="email@example.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className={inputCls}
          />
          <input
            aria-label={t('admin.accounts.password')}
            required
            type="password"
            placeholder={t('admin.accounts.password')}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={inputCls}
          />
          <select
            aria-label={t('admin.accounts.role')}
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className={inputCls}
          >
            <option value="Administrator">{statusLabel('Administrator')}</option>
          </select>
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
          >
            {busy ? t('admin.accounts.provisioning') : t('admin.accounts.provision')}
          </button>
        </form>
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={resolveMessage(error)} />}

      {accounts === null ? (
        <Loading />
      ) : accounts.length === 0 ? (
        <EmptyState title={t('admin.accounts.empty')} />
      ) : (
        <Card className="overflow-hidden">
          <p className="px-4 pt-3 text-xs text-mute sm:hidden">{t('common.swipeTable')}</p>
          <div className="overflow-x-auto" role="region" aria-label={t('admin.accounts.table')} tabIndex={0}>
            <table className="data-table min-w-[640px]">
              <thead>
                <tr>
                  <th className="px-4 py-2">{t('common.name')}</th>
                  <th className="px-4 py-2">{t('common.email')}</th>
                  <th className="px-4 py-2">{t('admin.accounts.roles')}</th>
                  <th className="px-4 py-2">{t('common.status')}</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {accounts.slice((currentPage - 1) * 10, currentPage * 10).map((a) => (
                  <tr key={a.account_id}>
                    <td className="px-4 py-2.5">{a.full_name || '—'}</td>
                    <td className="px-4 py-2.5">{a.email}</td>
                    <td className="px-4 py-2.5">{(a.roles || []).map(statusLabel).join(', ')}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {a.status === 'active' ? (
                        <button
                          type="button"
                          onClick={() => setStatus(a, 'disabled')}
                          className="text-sm font-medium text-rose-300 hover:underline"
                        >{t('admin.accounts.disable')}</button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setStatus(a, 'active')}
                          className="text-sm font-medium text-cyan-300 hover:underline"
                        >{t('admin.activate')}</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} />
        </Card>
      )}
    </div>
  )
}
