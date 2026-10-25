import { useState } from 'react'
import { Link } from 'react-router-dom'
import { t, useLocale, number, percent } from '../i18n'
import { Badge, Card, CardTitle, Pagination, inputCls, btnGhost } from './SharedComponents'
import { EmptyState } from './States'

export default function LeaderboardTable({ rows = [], full = false, assessmentId = '', studentView = false, currentAccountId = null }) {
  useLocale()
  const [rankingQuery, setRankingQuery] = useState('')
  const [rankingPage, setRankingPage] = useState(1)
  const ranking = rows.filter(row => `${row.full_name || ''} ${studentView ? '' : row.email || ''}`.toLowerCase().includes(rankingQuery.trim().toLowerCase()))
  const displayName = row => row.full_name || (!studentView && row.email) || t('studentRanking.unnamed')
  const Winner = studentView ? 'div' : Link
  const searchLabel = t(studentView ? 'studentRanking.search' : 'admin.analytics.rankingSearch')
  const rankingPages = Math.max(1, Math.ceil(ranking.length / 10))
  const activeRankingPage = Math.min(rankingPage, rankingPages)
  const leaders = rows.filter(row => row.average_pct != null).slice(0, 3)
  const leaderIds = new Set(leaders.map(row => row.account_id))
  const displayed = full ? ranking.slice((activeRankingPage - 1) * 10, activeRankingPage * 10) : rows.filter(row => !leaderIds.has(row.account_id)).slice(0, 5)
  return (
      <section aria-label={t('admin.analytics.rankingTitle')}>
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.analytics.rankingTitle')}><Badge>{number(rows.length)}</Badge></CardTitle>
          <div className="grid gap-3 border-b border-edge p-4 sm:items-center">
            <p className="text-xs leading-relaxed text-sub">{t(studentView ? 'studentRanking.help' : 'admin.analytics.rankingHelp')}</p>
            {full && <input type="search" className={inputCls} aria-label={searchLabel} placeholder={searchLabel} value={rankingQuery} onChange={e => { setRankingQuery(e.target.value); setRankingPage(1) }} />}
          </div>
          {!full && leaders.length > 0 && <div className="leaderboard-podium">
            {leaders.map((row, index) => <Winner key={row.account_id} {...(!studentView ? { to: `/admin/learners/${row.account_id}/competency` } : {})} className={`leaderboard-winner ${index === 0 ? 'leaderboard-winner-first' : ''}`}>
              <span className="leaderboard-place">{t('admin.analytics.rankingRank')} {number(row.rank)}</span>
              <span className="leaderboard-avatar" aria-hidden="true">{displayName(row).trim().charAt(0).toUpperCase()}</span>
              <strong className="break-words text-sm text-ink">{displayName(row)}</strong>
              {studentView && row.account_id === currentAccountId && <Badge tone="teal">{t('studentRanking.you')}</Badge>}
              <span className="text-xl font-semibold tabular-nums text-ink">{percent(row.average_pct, { maximumFractionDigits: 2 })}</span>
              <span className="text-xs text-mute">{number(row.assessments_graded)} {t('admin.analytics.rankingTests')}</span>
            </Winner>)}
          </div>}
          {!(full ? ranking : rows).length ? <div className="p-5"><EmptyState title={t('admin.analytics.rankingEmpty')} /></div> : displayed.length > 0 ? <>
            <div className="overflow-x-auto" role="region" aria-label={t('admin.analytics.rankingTitle')} tabIndex={0}>
              <table className="data-table min-w-[580px]">
                <thead><tr>
                  <th className="px-5 py-3">{t('admin.analytics.rankingRank')}</th>
                  <th className="px-5 py-3">{t('admin.analytics.rankingStudent')}</th>
                  <th className="px-5 py-3 text-right">{t('admin.analytics.rankingScore')}</th>
                  <th className="px-5 py-3 text-right">{t('admin.analytics.rankingTests')}</th>
                </tr></thead>
                <tbody>{displayed.map(row => <tr key={row.account_id} className={studentView && row.account_id === currentAccountId ? 'bg-accent/5' : undefined}>
                  <td className="px-5 py-3 font-semibold tabular-nums">{row.rank == null ? '—' : <span className={row.rank <= 3 ? 'inline-flex h-8 min-w-8 items-center justify-center rounded-lg border border-edge bg-elev text-ink' : 'text-sub'}>{number(row.rank)}</span>}</td>
                  <td className="px-5 py-3">{studentView ? <span className="font-medium text-ink">{displayName(row)}{row.account_id === currentAccountId && <span className="ml-2 text-xs text-accent">{t('studentRanking.you')}</span>}</span> : <Link className="text-left font-medium text-ink hover:underline" to={`/admin/learners/${row.account_id}/competency`}>{displayName(row)}</Link>}{!studentView && row.full_name && <p className="mt-1 text-xs text-mute">{row.email}</p>}</td>
                  <td className="px-5 py-3 text-right font-semibold tabular-nums">{row.average_pct == null ? <span className="text-xs font-normal text-mute">{t('admin.analytics.rankingUnscored')}</span> : percent(row.average_pct, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td className="px-5 py-3 text-right tabular-nums text-sub">{number(row.assessments_graded)}</td>
                </tr>)}</tbody>
              </table>
            </div>
            {full ? <div className="border-t border-edge p-3"><Pagination page={activeRankingPage} pageCount={rankingPages} onPageChange={setRankingPage} /></div> : null}
          </> : null}
          {!full && <div className="flex justify-end border-t border-edge p-4"><Link className={btnGhost} to={studentView ? '/leaderboard' : `/admin/leaderboard${assessmentId ? `?assessment_id=${assessmentId}` : ''}`}>{t('admin.analytics.rankingViewAll')}<span aria-hidden="true"> &rarr;</span></Link></div>}
        </Card>
      </section>

  )
}
