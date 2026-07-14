import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import TextDisplay, { spokenText } from './TextDisplay';

describe('spokenText', () => {
  it('removes ElevenLabs audio tags', () => {
    // The voice model performs these; a reader must never see them.
    expect(spokenText('[laughs] That is wild.')).toBe('That is wild.');
    expect(spokenText('Well... [pauses] let me think.')).toBe(
      'Well... let me think.'
    );
  });

  it('collapses the whitespace a stripped tag leaves behind', () => {
    expect(spokenText('Hello [sighs] there')).toBe('Hello there');
  });

  it('leaves untagged text untouched', () => {
    expect(spokenText('No tags here')).toBe('No tags here');
  });

  it('tolerates undefined', () => {
    expect(spokenText()).toBe('');
  });
});

describe('TextDisplay', () => {
  const noop = {};

  it('renders the line without its audio tags', () => {
    render(
      <TextDisplay
        isTextVisible
        items={[{ text: '[curious] So what changed?' }]}
        currentItemIndex={0}
        textContainerVariants={noop}
        textChildVariants={noop}
      />
    );

    expect(screen.queryByText(/\[curious\]/)).not.toBeInTheDocument();
    expect(screen.getByText('changed?')).toBeInTheDocument();
  });
});
