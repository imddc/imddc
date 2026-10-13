import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

for (const theme of ['dark', 'light']) {
  test(`${theme} repository chart shares the icon column's left origin`, () => {
    const svg = readFileSync(new URL(`../assets/community/languages-${theme}.svg`, import.meta.url), 'utf8');
    const title = svg.match(/data-testid="card-title"\s+transform="translate\(([^)]+)\)"/);
    const body = svg.match(/data-testid="lang-items" x="([^"]+)"/);
    assert.ok(title && body, 'Community card title and language body must be identifiable.');
    assert.equal(Number(title[1].split(',')[0]), 0, 'Chart title must not add a left gutter.');
    assert.equal(Number(body[1]), 0, 'Chart bar and legend must not add a left gutter.');
  });
}
