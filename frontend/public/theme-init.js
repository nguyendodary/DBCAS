(() => {
  const supported = ['light', 'dark', 'system']
  let preference = 'system'
  try {
    const saved = localStorage.getItem('dbcas_theme')
    if (supported.includes(saved)) preference = saved
  } catch { /* Use system preference when browser storage is unavailable. */ }

  let resolved = preference
  if (preference === 'system') {
    try { resolved = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light' }
    catch { resolved = 'light' }
  }

  document.documentElement.dataset.theme = resolved
  document.documentElement.dataset.themeMode = preference
  document.documentElement.style.colorScheme = resolved
})()
