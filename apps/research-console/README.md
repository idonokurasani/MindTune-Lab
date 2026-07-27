# MindTune Research Console

A React 18 + TypeScript 5 + Vite 5 frontend for the CLM-05 experimental API.

## Setup

```bash
cd apps/research-console
npm install
```

## Development

```bash
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000` by default. Set `VITE_API_TOKEN` in a `.env` file (do not commit) to send a bearer token on mutating requests. The token is never persisted in `localStorage`.

## Build

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

## E2E

Playwright is configured in `playwright.config.ts`. If browser installation fails (e.g. offline or missing system deps), the failure is documented here and the spec remains committed; it does not block other validations.

```bash
npx playwright install
npm run test:e2e
```

## Architecture

See `docs/architecture/CLM_05B_RESEARCH_CONSOLE.md`.
