export default function AccountAvatar({ account, className = 'h-8 w-8' }) {
  return <span className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-cyan-400/10 font-semibold text-cyan-500 ring-1 ring-inset ring-cyan-400/25 ${className}`}>
    {account?.avatar_url ? <img src={account.avatar_url} alt="" className="h-full w-full object-cover" /> : (account?.full_name || account?.email || '?').slice(0, 1).toUpperCase()}
  </span>
}
