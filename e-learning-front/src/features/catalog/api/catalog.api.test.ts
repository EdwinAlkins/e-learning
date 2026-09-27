import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { ContractViolationError } from '../../../shared/api/errors';
import { API_BASE_URL } from '../../../shared/api/http-client';
import { server } from '../../../test/server';
import { catalogApi } from './catalog.api';

const formationDto = {
  id: 'formation-42',
  name: 'Infrastructure',
  slug: 'infrastructure',
  chapters: [
    {
      id: 'chapter-7',
      name: 'Réseau',
      slug: 'reseau',
      position: 0,
      videos: [
        {
          id: 'video-9',
          title: 'TCP/IP',
          duration: 90,
          position: 1,
          kind: 'video',
          processing_status: 'ready',
          transcription_status: 'processing',
          summary_status: 'none',
          active_jobs: [
            {
              id: 'job-12',
              kind: 'transcription',
              status: 'running',
              progress: 35,
              message: 'Transcription',
            },
          ],
        },
      ],
      documents: [],
    },
  ],
};

describe('catalogApi', () => {
  it('valide et mappe le contrat canonique du catalogue', async () => {
    let requestedWith: string | null = null;
    server.use(
      http.get(`${API_BASE_URL}/formations`, ({ request }) => {
        requestedWith = request.headers.get('x-requested-with');
        return HttpResponse.json({ formations: [formationDto] });
      })
    );

    const formations = await catalogApi.getFormations();

    expect(requestedWith).toBe('XMLHttpRequest');
    expect(formations[0]).toEqual(
      expect.objectContaining({
        id: 'formation-42',
        chapters: [
          expect.objectContaining({
            id: 'chapter-7',
            videos: [
              expect.objectContaining({
                id: 'video-9',
                position: 1,
                sortOrder: 1,
              }),
            ],
          }),
        ],
      })
    );
  });

  it('échoue explicitement lorsque le backend change la forme du catalogue', async () => {
    server.use(
      http.get(`${API_BASE_URL}/formations`, () => HttpResponse.json({ data: [] }))
    );

    await expect(catalogApi.getFormations()).rejects.toBeInstanceOf(
      ContractViolationError
    );
  });

  it('refuse un identifiant non conforme au DTO réseau', async () => {
    server.use(
      http.get(`${API_BASE_URL}/formations`, () =>
        HttpResponse.json({ formations: [{ ...formationDto, id: 42 }] })
      )
    );

    await expect(catalogApi.getFormations()).rejects.toMatchObject({
      endpoint: 'GET /formations',
    });
  });
});
