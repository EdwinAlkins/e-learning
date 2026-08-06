'use client';

import { createContext, useContext, type ReactNode } from 'react';
import { useFormationBuilder } from './useFormationBuilder';

export type FormationBuilderContextValue = ReturnType<typeof useFormationBuilder>;

const FormationBuilderContext = createContext<FormationBuilderContextValue | null>(null);

export function FormationBuilderProvider({
  formationId,
  children,
}: {
  formationId: string;
  children: ReactNode;
}) {
  const value = useFormationBuilder(formationId);
  return (
    <FormationBuilderContext.Provider value={value}>{children}</FormationBuilderContext.Provider>
  );
}

export function useFormationBuilderContext(): FormationBuilderContextValue {
  const ctx = useContext(FormationBuilderContext);
  if (!ctx) {
    throw new Error('useFormationBuilderContext doit être utilisé dans FormationBuilderProvider');
  }
  return ctx;
}
