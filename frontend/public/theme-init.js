(() => {
  let preference = 'dark'
  try {
    const saved = localStorage.getItem('dbcas_theme')
    if (saved === 'light') preference = 'light'
    if (saved != null && saved !== preference) localStorage.setItem('dbcas_theme', preference)
  } catch { /* Dark is the default even when browser storage is unavailable. */ }
  document.documentElement.dataset.theme = preference
  document.documentElement.dataset.themeMode = preference
  document.documentElement.style.colorScheme = preference
})()
