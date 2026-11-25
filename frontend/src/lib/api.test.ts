import { describe, expect, it, vi, afterEach } from 'vitest';
import { recommend } from './api';

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.resetModules(); });

describe('recommend API client', () => {
  it('uses same-origin API routes for a production deployment', async () => {
    vi.resetModules();
    vi.stubEnv('PROD', true);
    vi.stubEnv('VITE_API_BASE_URL', '');
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetch);
    const client = await import('./api');
    await client.health();
    expect(fetch).toHaveBeenCalledWith('/api/health');
    await client.recommend({ nitrogen: 80, phosphorus: 45, potassium: 40, ph: 6.5, temperature_c: 24, humidity_pct: 72, rainfall_mm: 100 });
    expect(fetch).toHaveBeenCalledWith('/api/recommendations', expect.objectContaining({ method: 'POST' }));
  });
  it('posts field values and returns ranked candidates', async () => {
    const payload = { recommendation_id: 7, results: [{ crop: 'rice', score: 90 }], method: 'range distance', interpretation: 'similarity only', assumptions: [], unavailable_information: [], dataset_provenance: 'unverified' };
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
    vi.stubGlobal('fetch', fetch);
    const result = await recommend({ nitrogen: 80, phosphorus: 45, potassium: 40, ph: 6.5, temperature_c: 24, humidity_pct: 72, rainfall_mm: 100 });
    expect(result.recommendation_id).toBe(7);
    expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/recommendations$/), expect.objectContaining({ method: 'POST' }));
  });

  it('exposes API validation errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'invalid value' }) }));
    await expect(recommend({ nitrogen: 0, phosphorus: 0, potassium: 0, ph: 0, temperature_c: 0, humidity_pct: 0, rainfall_mm: 0 })).rejects.toThrow('invalid value');
  });
});
