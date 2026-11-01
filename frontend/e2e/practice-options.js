export async function openPracticeOptions(page) {
  const practice = page.getByText('Topic practice (optional)', { exact: true })
  await practice.waitFor({ state: 'visible' })
  if (!(await practice.locator('..').evaluate(node => node.open))) await practice.click()
  const options = page.getByText('Assessment options', { exact: true })
  if (!(await options.locator('..').evaluate(node => node.open))) await options.click()
}
