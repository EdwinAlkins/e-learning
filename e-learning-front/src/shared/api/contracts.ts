import type { ZodType } from 'zod';
import { ContractViolationError } from './errors';

export function parseApiResponse<T>(schema: ZodType<T>, data: unknown, endpoint: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    throw new ContractViolationError(endpoint, result.error);
  }
  return result.data;
}
