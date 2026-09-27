import { catalogDtoSchema, formationDtoSchema } from '../../../entities/formation/dto';
import { toFormation } from '../../../entities/formation/mappers';
import { parseApiResponse } from '../../../shared/api/contracts';
import { httpClient } from '../../../shared/api/http-client';
import type { Formation } from '../../../types';

export const catalogApi = {
  getFormations: async (): Promise<Formation[]> => {
    const response = await httpClient.get('/formations');
    const dto = parseApiResponse(catalogDtoSchema, response.data, 'GET /formations');
    return dto.formations.map(toFormation);
  },

  getFormation: async (formationId: string): Promise<Formation> => {
    const response = await httpClient.get(`/formations/${formationId}`);
    const dto = parseApiResponse(
      formationDtoSchema,
      response.data,
      'GET /formations/{formation_id}'
    );
    return toFormation(dto);
  },
};
