import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const coreDirectory = dirname(require.resolve('@stats-organization/github-readme-stats-core'));
// The pinned community package exposes its pure SVG renderer at this internal path.
const { renderTopLanguages } = await import(pathToFileURL(resolve(coreDirectory, 'cards/top-languages.js')));
const outputDirectory = fileURLToPath(new URL('../assets/community/', import.meta.url));
const owners = [['user', 'imddc'], ['organization', 'FizzLabs']];

/** Read all owned repositories and GitHub language bytes without persisting repository metadata. */
function fetchLanguages(kind, login) {
  const query = `query($login: String!, $cursor: String) {
    ${kind}(login: $login) {
      repositories(first: 100, after: $cursor${kind === 'user' ? ', ownerAffiliations: [OWNER]' : ''}) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isFork isPrivate
          languages(first: 100) {
            pageInfo { hasNextPage }
            edges { size node { name color } }
          }
        }
      }
    }
  }`;
  const languages = new Map();
  let cursor;
  let repositories = 0;
  let privateRepositories = 0;
  do {
    const args = ['api', 'graphql', '-f', `query=${query}`, '-f', `login=${login}`];
    if (cursor) args.push('-f', `cursor=${cursor}`);
    const result = JSON.parse(execFileSync('gh', args, { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }));
    if (result.errors?.length) throw new Error('GitHub returned errors; previous cards were preserved.');
    const connection = result.data?.[kind]?.repositories;
    if (!connection) throw new Error(`Cannot access repositories owned by ${login}.`);
    for (const repository of connection.nodes) {
      if (repository.isFork) continue;
      if (repository.languages.pageInfo.hasNextPage) throw new Error('Language pagination is required; refusing incomplete totals.');
      repositories++;
      if (repository.isPrivate) privateRepositories++;
      for (const { size, node } of repository.languages.edges) {
        const previous = languages.get(node.name);
        languages.set(node.name, { name: node.name, color: node.color ?? '#8b949e', size: size + (previous?.size ?? 0) });
      }
    }
    cursor = connection.pageInfo.hasNextPage ? connection.pageInfo.endCursor : null;
  } while (cursor);
  return { languages, repositories, privateRepositories };
}

/** Merge owners by actual code bytes and preserve the denominator with an Other bucket. */
function combineLanguages(results) {
  const totals = new Map();
  for (const { languages } of results) {
    for (const language of languages.values()) {
      const previous = totals.get(language.name);
      totals.set(language.name, { ...language, size: language.size + (previous?.size ?? 0) });
    }
  }
  const ranked = [...totals.values()].filter(language => language.size > 0).sort((a, b) => b.size - a.size);
  if (!ranked.length) throw new Error('No language data returned; previous cards were preserved.');
  const visible = ranked.slice(0, 8);
  const remainder = ranked.slice(8).reduce((sum, language) => sum + language.size, 0);
  if (remainder) visible.push({ name: 'Other', color: '#8b949e', size: remainder });
  return Object.fromEntries(visible.map(language => [language.name, language]));
}

/** Render dark and light cards; only aggregate language statistics enter the public assets. */
async function main() {
  const results = owners.map(([kind, login]) => fetchLanguages(kind, login));
  if (!results.some(result => result.privateRepositories > 0)) {
    throw new Error('No private repositories were accessible; refusing a public-only replacement.');
  }
  const languages = combineLanguages(results);
  const options = {
    layout: 'compact', langs_count: 9, card_width: 468, hide_border: true,
    custom_title: 'Repository mix', bg_color: '00000000', disable_animations: true,
  };
  await mkdir(outputDirectory, { recursive: true });
  for (const [theme, colors] of Object.entries({
    dark: { title_color: 'a4e5c9', text_color: 'd8e9e3' },
    light: { title_color: '173f38', text_color: '375b53' },
  })) {
    // Remove the community card's horizontal gutter to match the standalone README icons.
    const svg = renderTopLanguages(languages, { ...options, ...colors })
      .replace('transform="translate(25, 35)"', 'transform="translate(0, 35)"')
      .replace('data-testid="lang-items" x="25"', 'data-testid="lang-items" x="0"');
    const provenance = `<!-- Generated ${new Date().toISOString().slice(0, 10)} by github-readme-stats-core 2.2.1. imddc + FizzLabs; public and private; forks excluded; code bytes, not recent activity. -->\n`;
    await writeFile(resolve(outputDirectory, `languages-${theme}.svg`), provenance + svg.replace(/[ \t]+$/gm, '').trim() + '\n');
  }
  console.log(`Generated language cards from ${results.reduce((sum, result) => sum + result.repositories, 0)} repositories (${results.reduce((sum, result) => sum + result.privateRepositories, 0)} private).`);
}

await main();
