import { expect, test } from '@playwright/test';

const API_URL = 'http://localhost:8000';

test('un apprenant se connecte puis voit son catalogue', async ({ page }) => {
  let authenticated = false;

  await page.route(`${API_URL}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname === '/auth/me') {
      await route.fulfill({
        status: authenticated ? 200 : 401,
        contentType: 'application/json',
        body: JSON.stringify(
          authenticated
            ? {
                id: 'user-1',
                email: 'apprenant@example.com',
                full_name: 'Ada Lovelace',
                is_admin: false,
              }
            : { detail: 'Not authenticated' }
        ),
      });
      return;
    }

    if (url.pathname === '/auth/login' && request.method() === 'POST') {
      authenticated = true;
      await route.fulfill({ status: 204 });
      return;
    }

    if (url.pathname === '/formations') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          formations: [
            {
              id: 'formation-1',
              name: 'Infrastructure moderne',
              slug: 'infrastructure-moderne',
              chapters: [
                {
                  id: 'chapter-10',
                  name: 'Réseau',
                  slug: 'reseau',
                  position: 0,
                  videos: [
                    {
                      id: 'video-100',
                      title: 'Introduction',
                      duration: 600,
                      position: 1,
                      kind: 'video',
                      processing_status: 'ready',
                      transcription_status: 'none',
                      summary_status: 'none',
                      active_jobs: [],
                    },
                  ],
                  documents: [],
                },
              ],
            },
          ],
        }),
      });
      return;
    }

    if (url.pathname === '/progress/formations') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ progress: {} }),
      });
      return;
    }

    await route.abort('blockedbyclient');
  });

  await page.goto('/auth');
  await page.getByLabel('Email').fill('apprenant@example.com');
  await page.getByLabel('Mot de passe').fill('mot-de-passe');
  await page.getByRole('button', { name: 'Se connecter' }).click();

  await expect(page).toHaveURL('/');
  await expect(page.getByRole('heading', { name: 'Mes formations' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Infrastructure moderne' })).toBeVisible();
  await expect(page.getByText('1 chapitre · 1 vidéo')).toBeVisible();
});
