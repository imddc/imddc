# Profile language cards

The cards use the SVG renderer from [GitHub Stats Extended](https://github.com/stats-organization/github-stats-extended), pinned to version 2.2.1.

With Node.js 24 and GitHub CLI authenticated as an account that can read all intended `imddc` and `FizzLabs` repositories:

```sh
cd scripts
npm ci --ignore-scripts
npm run refresh
```

GitHub reports each repository's language sizes in bytes. The script sums these values across both owners, including public, private, and archived repositories and excluding forks. The top eight languages are displayed; all remaining languages are combined as Other. This measures repository code composition, not recent activity, time spent, proficiency, or code personally authored.

Review the two generated SVGs before committing. Only aggregate language percentages are published. Repository names, source code, and authentication credentials are never written into the assets. Authentication remains in GitHub CLI; the community library only renders the supplied totals locally. An account must have access to every intended repository; inaccessible private repositories cannot be detected or counted.
