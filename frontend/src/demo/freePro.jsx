import { useState } from 'react'
import { t, useLocale } from '../i18n'
import { Badge, Card, CardTitle, btnPrimary } from '../components/ui'

export const DEMO_FREE_SESSIONS = 3
export const DEMO_PRO_PRICE_VND = 99000
export const DEMO_PRO_DAYS = 30

export const DEMO_COST_SAMPLE = [
  { month: '2026-09', revenue: 198000, ai: 82000, hosting: 42000 },
  { month: '2026-10', revenue: 297000, ai: 118000, hosting: 48000 },
  { month: '2026-11', revenue: 396000, ai: 131000, hosting: 51000 },
]

export function demoFreeProEnabled() {
  return import.meta.env.VITE_DEMO_FREE_PRO === 'true'
}

export function DemoPlanPanel() {
  const { locale } = useLocale()
  const [plan, setPlan] = useState('free')
  if (!demoFreeProEnabled()) return null
  const pro = plan === 'pro'
  return (
    <div data-testid="demo-plan-panel">
      <Card className="mx-4 mt-4 border-cyan-400/30">
        <CardTitle title={t('ui.demo.planTitle')}>
          <Badge tone="teal">DEMO</Badge>
        </CardTitle>
        <div className="space-y-3 p-5 text-sm">
          <p className="font-semibold text-ink">
            {pro
              ? t('ui.demo.proPlan', {
                  price: DEMO_PRO_PRICE_VND.toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US'),
                  days: DEMO_PRO_DAYS,
                })
              : t('ui.demo.freePlan', { count: DEMO_FREE_SESSIONS })}
          </p>
          <p className="text-xs text-mute">{t('ui.demo.uiOnly')}</p>
          {!pro && (
            <button type="button" className={btnPrimary} onClick={() => setPlan('pro')}>
              {t('ui.demo.upgrade')}
            </button>
          )}
        </div>
      </Card>
    </div>
  )
}

export function DemoCostsPanel({ isAdmin = false }) {
  useLocale()
  if (!demoFreeProEnabled() || !isAdmin) return null
  const max = Math.max(...DEMO_COST_SAMPLE.map((row) => row.revenue))
  return (
    <div data-testid="demo-costs-panel">
      <Card>
        <CardTitle title={t('ui.demo.costsTitle')}>
          <Badge tone="teal">DEMO</Badge>
        </CardTitle>
        <div className="space-y-4 p-5 text-sm">
          <p className="text-xs text-mute">{t('ui.demo.sampleOnly')}</p>
          <ul className="space-y-2">
            {DEMO_COST_SAMPLE.map((row) => {
              const balance = row.revenue - row.ai - row.hosting
              return (
                <li key={row.month} className="space-y-1">
                  <div className="flex justify-between text-xs text-sub">
                    <span>{row.month}</span>
                    <span>
                      {t('ui.demo.revenue')} {row.revenue.toLocaleString('vi-VN')} · AI{' '}
                      {row.ai.toLocaleString('vi-VN')} · {t('ui.demo.hosting')}{' '}
                      {row.hosting.toLocaleString('vi-VN')} · {t('ui.demo.balance')}{' '}
                      {balance.toLocaleString('vi-VN')}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded bg-surface-hover" aria-hidden="true">
                    <div
                      className="h-full rounded bg-cyan-400"
                      style={{ width: `${Math.max(4, Math.round((row.revenue / max) * 100))}%` }}
                    />
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      </Card>
    </div>
  )
}
