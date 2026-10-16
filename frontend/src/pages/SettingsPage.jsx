import { t, useLocale, statusLabel } from '../i18n'
import { useAuth } from '../auth'
import { Card, CardTitle, HeroBand, IconChip, PageHeader, TagPill } from '../components/ui'
import LanguageSelector from '../components/LanguageSelector'
import ThemeSelector from '../components/ThemeSelector'
import heroPoster from '../assets/brand/nen1.jpg'
import heroVideo from '../assets/brand/video1.mp4'

// Shared settings view — the frontend branch's Cai_dat screens mapped onto
// what the real product actually supports: account identity (from /auth/me)
// plus the theme and language preferences that already persist locally.
export default function SettingsPage() {
  useLocale()
  const { account } = useAuth()
  const isAdmin = (account?.roles || []).includes('admin')
  return (
    <div className="space-y-6">
      {/* The learner prototype's settings screen opens on a dark video hero
          band; the admin prototype keeps a plain header surface. */}
      {isAdmin ? (
        <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />
      ) : (
        <HeroBand title={t('settings.title')} subtitle={t('settings.subtitle')} videoSrc={heroVideo} videoPoster={heroPoster} />
      )}

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <CardTitle title={t('settings.accountTitle')} />
          <div className="p-5">
            <div className="flex items-center gap-4">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cyan-400/10 text-lg font-bold text-cyan-300 ring-1 ring-inset ring-cyan-400/25">
                {(account?.full_name || account?.email || '?').slice(0, 1).toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="truncate text-base font-semibold text-ink">{account?.full_name || t('settings.noName')}</p>
                <p className="truncate text-sm text-mute">{account?.email}</p>
              </div>
            </div>
            <dl className="mt-5 space-y-3 border-t border-edge/70 pt-4 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <dt className="text-mute">{t('settings.roles')}</dt>
                <dd className="flex flex-wrap gap-1.5">
                  {(account?.roles || []).map((role) => (
                    <TagPill key={role} accent>{statusLabel(role)}</TagPill>
                  ))}
                </dd>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <dt className="text-mute">{t('common.status')}</dt>
                <dd><TagPill>{statusLabel(account?.status || 'active')}</TagPill></dd>
              </div>
            </dl>
          </div>
        </Card>

        <Card>
          <CardTitle title={t('settings.appearanceTitle')} />
          <div className="p-5">
            <p className="text-sm text-mute">{t('settings.appearanceBody')}</p>
            <dl className="mt-5 space-y-4 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <dt className="flex items-center gap-3 text-sub">
                  <IconChip name="monitor" />
                  <span>
                    <span className="block font-medium text-ink">{t('theme.select')}</span>
                    <span className="block text-xs text-mute">{t('settings.themeHint')}</span>
                  </span>
                </dt>
                <dd><ThemeSelector /></dd>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-edge/70 pt-4">
                <dt className="flex items-center gap-3 text-sub">
                  <IconChip name="book" />
                  <span>
                    <span className="block font-medium text-ink">{t('common.language')}</span>
                    <span className="block text-xs text-mute">{t('settings.languageHint')}</span>
                  </span>
                </dt>
                <dd><LanguageSelector /></dd>
              </div>
            </dl>
          </div>
        </Card>
      </section>

      <p className="flex items-center gap-2 text-xs text-faint">
        <span className="eyebrow eyebrow-no-dot">{t('settings.storageNote')}</span>
      </p>
    </div>
  )
}
