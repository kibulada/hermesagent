# AI Test Generation Prompt Template

You are an expert QA automation engineer. Generate Playwright test code to verify the following Acceptance Criteria.

## Ticket Information
- **ID**: PP#{ticket_id}
- **Subject**: {subject}

## Acceptance Criteria
{ac_text}

## Your Task
Generate a COMPLETE Playwright test function that:
1. Verifies EACH point in the AC with specific assertions
2. Uses realistic CSS selectors based on common patterns
3. Includes proper waits and error handling

## Selector Hints (Common UI Elements in SIMRS)
{selector_hints}

## CRUD Pattern Recognition
- **Hapus/Remove** → `await expect(page.locator('...')).toBeHidden();`
- **Tampil/Muncul** → `await expect(page.locator('...')).toBeVisible();`
- **Simpan/Save** → `await page.click('button:has-text("Simpan")');`
- **Config dari X** → verify element uses data from config source

## Output Format
Return ONLY the test function (no imports, no describe block):

```typescript
test('PP#{ticket_id} - [descriptive name]', async ({{ page }}) => {{
  // AC#1: [description]
  await page.goto('/relevant-path');
  await expect(page.locator('.selector')).toBeVisible();
  
  // AC#2: [description]
  await page.click('button.action');
  await expect(page.locator('.result')).toContainText('expected');
}});
```

## Rules
- NO placeholder comments like "TODO" or "implement later"
- EACH AC point must have executable assertion
- Use fallback selector chains if uncertain
- Add explicit waits for dynamic content
- Return ONLY TypeScript code, no explanation
- CRITICAL: Your response must start with ```typescript and end with ```. NO other text before or after the code block.
