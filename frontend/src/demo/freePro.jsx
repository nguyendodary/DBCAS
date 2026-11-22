import { useState } from 'react'
import { useLocale } from '../i18n'
import { Badge, Card, CardTitle, btnPrimary } from '../components/ui'

export const DEMO_FREE_PRO_FLAG = 'VITE_DEMO_FREE_PRO'
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
  const vi = locale === 'vi'
  const pro = plan === 'pro'
  return (
    <div data-testid="demo-plan-panel">
      <Card className="mx-4 mt-4 border-cyan-400/30">
        <CardTitle title={vi ? 'Gói demo' : 'Demo plan'}>
          <Badge tone="teal">DEMO</Badge>
        </CardTitle>
        <div className="space-y-3 p-5 text-sm">
          <p className="font-semibold text-ink">
            {pro
              ? vi
                ? `Pro (Demo) · ${DEMO_PRO_PRICE_VND.toLocaleString('vi-VN')} VND / ${DEMO_PRO_DAYS} ngày`
                : `Pro (Demo) · ${DEMO_PRO_PRICE_VND.toLocaleString('en-US')} VND / ${DEMO_PRO_DAYS} days`
              : vi
                ? `Free · ${DEMO_FREE_SESSIONS} phiên mỗi tháng`
                : `Free · ${DEMO_FREE_SESSIONS} sessions per month`}
          </p>
          <p className="text-xs text-mute">
            {vi
              ? 'Mô phỏng giao diện; không có thanh toán, không gọi API, không lưu dữ liệu.'
              : 'UI simulation only; no payment, no API call, no stored data.'}
          </p>
          {!pro && (
            <button type="button" className={btnPrimary} onClick={() => setPlan('pro')}>
              {vi ? 'Nâng cấp Pro (Demo)' : 'Upgrade to Pro (Demo)'}
            </button>
          )}
        </div>
      </Card>
    </div>
  )
}

export function DemoCostsPanel({ isAdmin = false }) {
  const { locale } = useLocale()
  if (!demoFreeProEnabled() || !isAdmin) return null
  const vi = locale === 'vi'
  const max = Math.max(...DEMO_COST_SAMPLE.map((row) => row.revenue))
  return (
    <div data-testid="demo-costs-panel">
      <Card>
        <CardTitle title={vi ? 'Chi phí demo (mẫu tĩnh)' : 'Demo costs (static sample)'}>
          <Badge tone="teal">DEMO</Badge>
        </CardTitle>
        <div className="space-y-4 p-5 text-sm">
          <p className="text-xs text-mute">
            {vi
              ? 'Dữ liệu mẫu, không có prompt/SQL/answer; chỉ Administrator thấy.'
              : 'Sample data only; no prompts/SQL/answers; Administrator-only.'}
          </p>
          <ul className="space-y-2">
            {DEMO_COST_SAMPLE.map((row) => {
              const balance = row.revenue - row.ai - row.hosting
              return (
                <li key={row.month} className="space-y-1">
                  <div className="flex justify-between text-xs text-sub">
                    <span>{row.month}</span>
                    <span>
                      {vi ? 'Doanh thu' : 'Revenue'} {row.revenue.toLocaleString('vi-VN')} ·{' '}
                      {vi ? 'AI' : 'AI'} {row.ai.toLocaleString('vi-VN')} ·{' '}
                      {vi ? 'Hạ tầng' : 'Hosting'} {row.hosting.toLocaleString('vi-VN')} ·{' '}
                      {vi ? 'Còn lại' : 'Balance'} {balance.toLocaleString('vi-VN')}
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
