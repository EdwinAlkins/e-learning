import { expect, test } from '@playwright/test';

const API_URL = 'http://localhost:8000';

const videos = [
  {
    id: 'video-1',
    title: 'Introduction',
    duration: 60,
    position: 1,
    kind: 'video',
    processing_status: 'ready',
    transcription_status: 'none',
    summary_status: 'none',
    active_jobs: [],
  },
  {
    id: 'video-2',
    title: 'Composants',
    duration: 120,
    position: 2,
    kind: 'video',
    processing_status: 'ready',
    transcription_status: 'none',
    summary_status: 'none',
    active_jobs: [],
  },
];

test('un admin réordonne une vidéo dans le Studio', async ({ page }) => {
  let submittedOrder: string[] | null = null;

  await page.route(`${API_URL}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname === '/auth/me') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'admin-1',
          email: 'admin@example.com',
          full_name: 'Grace Hopper',
          is_admin: true,
        }),
      });
      return;
    }

    if (url.pathname === '/formations/formation-1' && request.method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'formation-1',
          name: 'Architecture',
          slug: 'architecture',
          chapters: [
            {
              id: 'chapter-1',
              name: 'Fondations',
              slug: 'fondations',
              position: 0,
              videos,
              documents: [],
            },
          ],
        }),
      });
      return;
    }

    if (url.pathname === '/chapters/chapter-1/videos/order' && request.method() === 'PUT') {
      submittedOrder = request.postDataJSON().video_ids;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'chapter-1',
          name: 'Fondations',
          slug: 'fondations',
          position: 0,
          videos: [
            { ...videos[1], position: 1 },
            { ...videos[0], position: 2 },
          ],
          documents: [],
        }),
      });
      return;
    }

    await route.abort('blockedbyclient');
  });

  await page.goto('/studio/formation/formation-1');
  await expect(page.getByLabel('Titre de la formation')).toHaveValue('Architecture');

  await page.getByRole('button', { name: 'Monter', exact: true }).nth(1).click();

  await expect.poll(() => submittedOrder).toEqual(['video-2', 'video-1']);
});
