import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import ProgressIndicator from './ProgressIndicator';
import { usePlayerStore } from '../stores/player.store';

beforeEach(() => {
  usePlayerStore.setState({
    currentVideoId: null,
    currentTime: 0,
    isPlaying: false,
  });
});

describe('ProgressIndicator', () => {
  it('affiche le temps courant, la durée et le pourcentage', () => {
    usePlayerStore.setState({ currentTime: 30 });

    render(<ProgressIndicator duration={120} rightElement={<span>En lecture</span>} />);

    expect(screen.getByText('00:30 / 02:00')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
    expect(screen.getByText('En lecture')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '25');
  });

  it('évite une division par zéro lorsque la durée est inconnue', () => {
    usePlayerStore.setState({ currentTime: 30 });

    render(<ProgressIndicator duration={0} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  });
});
