import { t, useLocale, message, statusLabel } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Card, ConfirmDialog, Notice, Pagination, StatusBadge, inputCls, focusDialogTrigger } from '../../components/SharedComponents'
import { AdminPageHeader, FilterBar } from '../../components/AdminComponents'

// UC04 — provision accounts (start disabled) and activate verified ones.
export default function Accounts_Admin() {
  useLocale()
  const [accounts, setAccounts] = useState(null)
  const [capability, setCapability] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'Administrator' })
  const [busy, setBusy] = useState(false)
  const [busyAccount, setBusyAccount] = useState(null)
  const [roleTarget, setRoleTarget] = useState(null)
  const [roleError, setRoleError] = useState('')
  const [roleBusy, setRoleBusy] = useState(false)
  const roleGuard = useRef(false)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ q: '', role: '', status: '' })

  const load = useCallback(() => {
    setError('')
    return Promise.all([
      api.get('/admin/accounts'),
      api.get('/admin/role-management/capability'),
    ])
      .then(([accountsResponse, capabilityResponse]) => {
        setAccounts(accountsResponse.data)
        setCapability(capabilityResponse.data)
      })
      .catch((e) => {
        setError(apiMessage(e))
        setAccounts([])
        setCapability(null)
      })
  }, [])

  useEffect(() => { load() }, [load])

  async function provision(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/admin/accounts', form)
      setNotice(message('admin.accounts.provisioned', { email: form.email }))
      setForm({ name: '', email: '', password: '', role: 'Administrator' })
      await load()
    } catch (e2) {
      setError(apiMessage(e2))
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(account, status) {
    setError('')
    setBusyAccount(account.account_id)
    try {
      await api.patch(`/admin/accounts/${account.account_id}`, { status })
      await load()
    } catch (e) {
      setError(apiMessage(e))
    } finally {
      setBusyAccount(null)
    }
  }

  function requestRoleChange(event, account, role) {
    focusDialogTrigger(event)
    setRoleError('')
    setRoleTarget({ account, role })
  }

  async function confirmRoleChange() {
    if (roleGuard.current || !roleTarget) return
    roleGuard.current = true
    setRoleBusy(true)
    setRoleError('')
    const currentRole = roleTarget.account.roles?.includes('Administrator') ? 'Administrator' : 'Learner'
    try {
      await api.patch(`/admin/accounts/${roleTarget.account.account_id}/role`, {
        role: roleTarget.role,
        expected_role: currentRole,
      })
      setNotice(message(roleTarget.role === 'Administrator' ? 'admin.accounts.roleGranted' : 'admin.accounts.roleRevoked', {
        email: roleTarget.account.email,
      }))
      setRoleTarget(null)
      await load()
    } catch (e) {
      setRoleError(apiMessage(e))
    } finally {
      roleGuard.current = false
      setRoleBusy(false)
    }
  }

  const roleOptions = [...new Set((accounts || []).flatMap((a) => a.roles || []))]
  const query = filters.q.trim().toLowerCase()
  const visibleAccounts = (accounts || []).filter((a) =>
    (!query || (a.full_name || '').toLowerCase().includes(query) || a.email.toLowerCase().includes(query))
    && (!filters.role || (a.roles || []).includes(filters.role))
    && (!filters.status || a.status === filters.status))
  const activeFilterCount = Object.values(filters).filter(Boolean).length

  const pageCount = Math.ceil(visibleAccounts.length / 10)
  const currentPage = Math.min(page, pageCount || 1)

  return (
    <div data-admin-view="accounts" className="space-y-4">
      <AdminPageHeader icon="users"
        title={t('admin.accounts.title')}
        subtitle={
          t('admin.accounts.intro')
        }
      />

      {capability?.can_manage_roles ? <Card className="p-4 sm:p-5">
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
      </Card> : capability ? <Notice>{t('admin.accounts.roleManagerOnly')}</Notice> : null}

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={resolveMessage(error)} />}

      {accounts === null ? (
        <Loading />
      ) : accounts.length === 0 ? (
        <EmptyState title={t('admin.accounts.empty')} />
      ) : (
        <>
        <FilterBar
          activeCount={activeFilterCount}
          onClear={() => { setFilters({ q: '', role: '', status: '' }); setPage(1) }}
        >
          <input
            aria-label={t('admin.accounts.search')}
            placeholder={t('admin.accounts.searchPlaceholder')}
            value={filters.q}
            onChange={(e) => { setFilters({ ...filters, q: e.target.value }); setPage(1) }}
            className={`${inputCls} !py-1.5 min-w-[10rem] flex-1`}
          />
          <select value={filters.role} aria-label={t('admin.accounts.filterRole')}
            onChange={(e) => { setFilters({ ...filters, role: e.target.value }); setPage(1) }}
            className="rounded-md border border-edge2 bg-panel px-2 py-1.5 text-sm text-ink focus:border-cyan-400/60 focus:outline-none">
            <option value="">{t('admin.accounts.allRoles')}</option>
            {roleOptions.map((role) => <option key={role} value={role}>{statusLabel(role)}</option>)}
          </select>
          <select value={filters.status} aria-label={t('admin.accounts.filterStatus')}
            onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1) }}
            className="rounded-md border border-edge2 bg-panel px-2 py-1.5 text-sm text-ink focus:border-cyan-400/60 focus:outline-none">
            <option value="">{t('admin.accounts.allStatuses')}</option>
            <option value="active">{statusLabel('active')}</option>
            <option value="disabled">{statusLabel('disabled')}</option>
          </select>
        </FilterBar>
        <Card className="overflow-hidden">
          <p className="px-4 pt-3 text-xs text-mute sm:hidden">{t('common.swipeTable')}</p>
          <div className="overflow-x-auto" role="region" aria-label={t('admin.accounts.table')} tabIndex={0}>
            <table className="data-table min-w-[560px]">
              <thead>
                <tr>
                  <th className="px-4 py-2">{t('admin.accounts.user')}</th>
                  <th className="px-4 py-2">{t('admin.accounts.roles')}</th>
                  <th className="px-4 py-2">{t('common.status')}</th>
                  <th className="px-4 py-2">{t('admin.accounts.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {visibleAccounts.slice((currentPage - 1) * 10, currentPage * 10).map((a) => (
                  <tr key={a.account_id}>
                    <td className="px-4 py-2.5">
                      {a.full_name || '—'}
                      <span className="block text-xs text-mute">{a.email}</span>
                    </td>
                    <td className="px-4 py-2.5">{(a.roles || []).map(statusLabel).join(', ')}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {a.status === 'active' ? (
                        <button
                          type="button"
                          disabled={busyAccount === a.account_id || a.account_id === capability?.account_id || ((a.roles || []).includes('Administrator') && !capability?.can_manage_roles)}
                          onClick={() => setStatus(a, 'disabled')}
                          className="text-sm font-medium text-rose-300 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                        >{t('admin.accounts.disable')}</button>
                      ) : (
                        <button
                          type="button"
                          disabled={busyAccount === a.account_id || ((a.roles || []).includes('Administrator') && !capability?.can_manage_roles)}
                          onClick={() => setStatus(a, 'active')}
                          className="text-sm font-medium text-cyan-300 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                        >{t('admin.activate')}</button>
                      )}
                      {capability?.can_manage_roles && a.account_id !== capability.account_id && (
                        <button
                          type="button"
                          disabled={roleBusy || busyAccount === a.account_id || (a.status !== 'active' && !a.roles?.includes('Administrator'))}
                          onClick={(event) => requestRoleChange(event, a, a.roles?.includes('Administrator') ? 'Learner' : 'Administrator')}
                          className="ml-3 text-sm font-medium text-cyan-300 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                        >{a.roles?.includes('Administrator') ? t('admin.accounts.revokeRole') : t('admin.accounts.grantRole')}</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} />
        </Card>
        </>
      )}
      <ConfirmDialog
        open={Boolean(roleTarget)}
        title={t(roleTarget?.role === 'Administrator' ? 'admin.accounts.grantTitle' : 'admin.accounts.revokeTitle')}
        confirmLabel={roleBusy ? t('common.saving') : t(roleTarget?.role === 'Administrator' ? 'admin.accounts.grantRole' : 'admin.accounts.revokeRole')}
        cancelLabel={t('common.cancel')}
        busy={roleBusy}
        onConfirm={confirmRoleChange}
        onCancel={() => { setRoleTarget(null); setRoleError('') }}
      >
        <p>{t(roleTarget?.role === 'Administrator' ? 'admin.accounts.grantHelp' : 'admin.accounts.revokeHelp')}</p>
        {roleTarget && <p className="mt-2 font-medium text-ink">{roleTarget.account.full_name || roleTarget.account.email}</p>}
        {roleError && <p role="alert" className="mt-3 text-sm text-rose-300">{resolveMessage(roleError)}</p>}
      </ConfirmDialog>
    </div>
  )
}
