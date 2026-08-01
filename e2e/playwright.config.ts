import { defineConfig, devices } from '@playwright/test'

/**
 * The suite boots its own backend with rate limiting disabled: the auth rate
 * limiters are per client address and the whole suite shares one address, so
 * the default limits (10 logins, 5 registrations per minute) would make the
 * full run non-deterministic. Everything else (JWT secret, demo/admin accounts)
 * is provided here so e2e never depends on a developer's local .env.
 */
const e2eBackendEnv = {
  ...process.env,
  DATABASE_URL: 'sqlite:///./fridgital-e2e.db',
  AUTH_LOGIN_RATE_PER_MINUTE: '0',
  AUTH_REGISTER_RATE_PER_MINUTE: '0',
  SEED_DEMO_DATA: 'true',
  FRIDGE_PAL_JWT_SECRET: 'e2e-secret-at-least-thirty-two-characters-long!!',
  FRIDGE_PAL_DEMO_PASSWORD: 'demo-pass-123',
  FRIDGE_PAL_ADMIN_USERNAME: 'admin',
  FRIDGE_PAL_ADMIN_PASSWORD: 'admin-pass-123',
  RECIPE_PROVIDER_MODE: 'fixture',
}

export default defineConfig({
  testDir: './tests',
  webServer: [
    {
      command: 'npm run dev --prefix ../frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd ../backend && .venv/bin/uvicorn app.main:app --port 8000',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: !process.env.CI,
      env: e2eBackendEnv,
    },
  ],
  use: {
    baseURL: 'http://localhost:5173',
  },
  projects: [
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } },
    },
    {
      name: 'desktop-chrome',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
  ],
})
