import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Card, Notice, PageHeader, StatusBadge, inputCls } from '../../components/ui'

// UC04 — provision accounts (start disabled) and activate verified ones.
export default function AdminAccountsPage() {
  const [accounts, setAccounts] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'Administrator' })
  const [busy, setBusy] = useState(false)

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
      setNotice(`Provisioned ${form.email} — activate it after verifying the person.`)
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

  return (
    <div className="space-y-4">
      <AdminNav />
      <PageHeader
        title="Accounts"
        subtitle={
          <>
            Provisioned accounts start <strong>disabled</strong> and cannot
            log in until you activate them after verifying the intended
            person.
          </>
        }
      />

      <Card className="p-4">
        <form onSubmit={provision} className="grid gap-2 sm:grid-cols-5">
          <input
            required
            placeholder="Full name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className={inputCls}
          />
          <input
            required
            type="email"
            placeholder="email@example.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className={inputCls}
          />
          <input
            required
            type="password"
            placeholder="Temporary password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={inputCls}
          />
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className={inputCls}
          >
            <option>Administrator</option>
            <option>Learner</option>
          </select>
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {busy ? 'Provisioning…' : 'Provision'}
          </button>
        </form>
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} />}

      {accounts === null ? (
        <Loading />
      ) : accounts.length === 0 ? (
        <EmptyState title="No accounts" />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-2">Name</th>
                  <th className="px-4 py-2">Email</th>
                  <th className="px-4 py-2">Roles</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y">
                {accounts.map((a) => (
                  <tr key={a.account_id}>
                    <td className="px-4 py-2.5">{a.full_name || '—'}</td>
                    <td className="px-4 py-2.5">{a.email}</td>
                    <td className="px-4 py-2.5">{(a.roles || []).join(', ')}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {a.status === 'active' ? (
                        <button
                          type="button"
                          onClick={() => setStatus(a, 'disabled')}
                          className="text-sm font-medium text-red-600 hover:underline"
                        >
                          Disable
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setStatus(a, 'active')}
                          className="text-sm font-medium text-blue-600 hover:underline"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
