import { defineConfig } from 'vitest/config';
import { loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({ mode }) => {
 const env = loadEnv(mode, '.', '');
 return {
  plugins: [react()],
  // One Vercel domain serves both UI and API, including preview deployments.
  define: env.VERCEL === '1' ? { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('/api') } : {},
  test: { environment: 'jsdom' }
 };
});
