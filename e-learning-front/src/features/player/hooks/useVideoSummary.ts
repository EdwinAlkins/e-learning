'use client';

import { useState } from 'react';
import type { Video } from '../../../types';
import {
  useUpdateVideoSummaryMutation,
  useVideoSummaryQuery,
} from '../queries/player.queries';

export function useVideoSummary(videoId: string, status: Video['summary_status']) {
  const summaryQuery = useVideoSummaryQuery(videoId, status === 'ready');
  const updateSummary = useUpdateVideoSummaryMutation(videoId);
  const [showSummary, setShowSummary] = useState(false);
  const [summaryRequested, setSummaryRequested] = useState(false);
  const [isEditingSummary, setIsEditingSummary] = useState(false);
  const [editSummaryContent, setEditSummaryContent] = useState('');

  const toggleSummary = async () => {
    if (summaryQuery.data !== undefined) {
      setShowSummary((visible) => !visible);
      return;
    }
    setSummaryRequested(true);
    setShowSummary(true);
    const result = await summaryQuery.refetch();
    if (result.error) setShowSummary(false);
  };

  const openSummary = () => {
    setSummaryRequested(true);
    setShowSummary(true);
  };

  const startEditing = () => {
    if (summaryQuery.data) {
      setIsEditingSummary(true);
      setEditSummaryContent(summaryQuery.data);
    }
  };

  const cancelEditing = () => {
    setIsEditingSummary(false);
    setEditSummaryContent('');
  };

  const saveSummary = async () => {
    const content = editSummaryContent.trim();
    if (!content) throw new Error('Le résumé ne peut pas être vide');
    await updateSummary.mutateAsync(content);
    cancelEditing();
  };

  return {
    summary: summaryQuery.data ?? null,
    summaryLoading: summaryQuery.isFetching,
    summaryError:
      summaryRequested && summaryQuery.error
        ? summaryQuery.error instanceof Error
          ? summaryQuery.error.message
          : 'Échec du chargement du résumé'
        : null,
    showSummary,
    isEditingSummary,
    editSummaryContent,
    setEditSummaryContent,
    savingSummary: updateSummary.isPending,
    toggleSummary,
    openSummary,
    startEditing,
    cancelEditing,
    saveSummary,
  };
}
