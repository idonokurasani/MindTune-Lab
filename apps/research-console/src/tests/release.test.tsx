import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import { ReleasePage } from '../pages/ReleasePage';

const mkResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const releaseInfo = {
  release_id: 'clm10-test',
  semantic_version: '0.10.0-rc.1',
  git_commit_sha: 'abc123',
  base_sha: 'def456',
  dirty_tree: false,
  build_timestamp: '2026-01-01T00:00:00+00:00',
  status: 'release_candidate',
};

const releaseManifest = {
  ...releaseInfo,
  release_candidate_number: 1,
  python_version: '3.14.0',
  node_version: '26.5.0',
  package_versions: {},
  frontend_build_checksum: null,
  backend_package_checksum: 'sha256',
  configuration_schema_version: '1.0.0',
  event_schema_versions: {},
  protocol_versions: {},
  curriculum_versions: {},
  calibration_algorithm_versions: {},
  estimator_version: '1.0.0',
  control_policy_version: '1.0.0',
  safety_policy_version: '1.0.0',
  voice_cache_contract_version: '1.0.0',
  audio_renderer_version: '1.0.0',
  api_version: 'v1',
  research_console_version: '0.10.0-rc.1',
  storage_migration_version: '0001',
  supported_deployment_modes: [],
  known_limitations: ['FC11 hardware validation not run'],
  container_image_digest: null,
  provenance: 'test',
};

const validation = {
  status: 'conditional_go',
  hardware_tests: 'blocked_by_hardware',
  validation_matrix_path: 'docs/release/CLM_10_VALIDATION_MATRIX.md',
};

const limitations = {
  known_limitations: ['FC11 hardware validation not run'],
  limitations_path: 'docs/release/CLM_10_KNOWN_LIMITATIONS.md',
};

const evidence = {
  evidence_index: 'docs/release/evidence/clm-10/README.md',
  status: 'indexed',
};

const responses: Record<string, unknown> = {
  '/api/v1/release': releaseInfo,
  '/api/v1/release/manifest': releaseManifest,
  '/api/v1/release/validation': validation,
  '/api/v1/release/limitations': limitations,
  '/api/v1/release/evidence': evidence,
};

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: RequestInfo | URL) => {
      const key = typeof url === 'string' ? url : url.toString();
      const suffix = Object.keys(responses).find((k) => key.endsWith(k)) || '';
      const body = suffix ? responses[suffix] : { error: 'not found' };
      const status = suffix ? 200 : 404;
      return mkResponse(body, status);
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('CLM-10 Release Candidate page', () => {
  it('displays release identity and validation status', async () => {
    render(<ReleasePage />);
    await waitFor(() => {
      expect(screen.getByText('Version: 0.10.0-rc.1')).toBeDefined();
      expect(screen.getByText('Status: release_candidate')).toBeDefined();
      expect(screen.getByText('Hardware tests: blocked_by_hardware')).toBeDefined();
    });
  });
});
