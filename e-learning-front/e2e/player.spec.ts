import { expect, test } from '@playwright/test';

const API_URL = 'http://localhost:8000';

test('un apprenant ouvre une vidéo et retrouve les panneaux du lecteur', async ({ page }) => {
  await page.route(`${API_URL}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname === '/auth/me') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-1',
          email: 'apprenant@example.com',
          full_name: 'Ada Lovelace',
          is_admin: false,
        }),
      });
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
                  id: 'chapter-1',
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
                      processing_status: 'processing',
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

    if (url.pathname === '/progress/video-100') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ last_position: 42 }),
      });
      return;
    }

    if (url.pathname === '/notes/video-100') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
      return;
    }

    await route.abort('blockedbyclient');
  });

  await page.goto('/player/video-100');

  await expect(page.getByRole('heading', { name: 'Introduction' })).toBeVisible();
  await expect(page.getByText('Infrastructure moderne')).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Notes' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Documents' })).toBeVisible();
  await expect(page.getByText('Aucune note pour le moment.')).toBeVisible();
});
