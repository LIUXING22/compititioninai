import { expect, test, type Page } from '@playwright/test'

async function clickOption(page: Page, key: string) {
  await page.locator('button.option-btn-default, button.option-btn-selected').evaluateAll(
    (buttons, expectedKey) => {
      const button = buttons.find(
        (item) => item.querySelector('span')?.textContent?.trim() === expectedKey,
      ) as HTMLButtonElement | undefined
      if (!button) throw new Error(`Option ${expectedKey} not found`)
      button.click()
    },
    key,
  )
}

test('wrong practice answer can be explained', async ({ page }) => {
  await page.goto('/practice')
  const responsePromise = page.waitForResponse((response) =>
    response.url().includes('/api/practice/start') && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: '开始练习' }).click()
  const response = await responsePromise
  const body = await response.json()
  const question = body.questions[0]
  const wrongKey = Object.keys(question.options).find((key) => !question.answer.includes(key))
  expect(wrongKey).toBeTruthy()

  await clickOption(page, wrongKey)
  const explainButton = page.getByRole('button', { name: 'AI 解释这道错题' })
  await expect(explainButton).toBeVisible()
  await explainButton.click()

  await expect(page.getByRole('heading', { name: '错题解析' })).toBeVisible({ timeout: 45_000 })
  await expect(page.getByText(/OpenAI|本地解析/).first()).toBeVisible()
  await page.screenshot({ path: 'test-results/wrong-answer-desktop.png', fullPage: true })
})

test('multiple-choice practice supports selecting before submit', async ({ page }) => {
  await page.goto('/practice')
  await page.getByText('多选题专练', { exact: true }).click()
  const responsePromise = page.waitForResponse((response) =>
    response.url().includes('/api/practice/start') && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: '开始练习' }).click()
  const response = await responsePromise
  const body = await response.json()
  expect(body.questions[0].type).toBe('multiple')

  await clickOption(page, 'A')
  await clickOption(page, 'B')
  await expect(page.locator('button.option-btn-selected')).toHaveCount(2)
  await page.getByRole('button', { name: '提交多选答案' }).click()
  await expect(page.getByRole('button', { name: /下一题|完成/ })).toBeVisible()
})

test('mobile layout has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/practice')
  const hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(hasOverflow).toBe(false)
  await page.screenshot({ path: 'test-results/practice-mobile.png', fullPage: true })
})
