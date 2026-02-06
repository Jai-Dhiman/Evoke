import { useCallback } from 'react';
import type { MoodSliders as MoodSlidersType } from '../types';

interface MoodSlidersProps {
  sliders: MoodSlidersType;
  onChange: (sliders: MoodSlidersType) => void;
  disabled?: boolean;
}

interface SliderConfig {
  key: keyof MoodSlidersType;
  label: string;
  leftLabel: string;
  rightLabel: string;
}

const sliderConfigs: SliderConfig[] = [
  { key: 'energy', label: 'Energy', leftLabel: 'Calm', rightLabel: 'Intense' },
  { key: 'valence', label: 'Mood', leftLabel: 'Dark', rightLabel: 'Bright' },
  { key: 'tempo', label: 'Pace', leftLabel: 'Slow', rightLabel: 'Fast' },
  { key: 'texture', label: 'Texture', leftLabel: 'Simple', rightLabel: 'Complex' },
];

export function MoodSliders({ sliders, onChange, disabled = false }: MoodSlidersProps) {
  const handleChange = useCallback(
    (key: keyof MoodSlidersType, value: number) => {
      onChange({
        ...sliders,
        [key]: value / 100,
      });
    },
    [sliders, onChange]
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontStyle: 'italic',
        fontSize: '18px',
        fontWeight: 400,
        color: 'var(--color-text)',
        margin: 0,
      }}>
        Adjust Mood
      </h3>

      {sliderConfigs.map((config) => {
        const value = Math.round(sliders[config.key] * 100);
        return (
          <div key={config.key} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
            }}>
              <span style={{
                fontFamily: 'var(--font-body)',
                fontSize: '11px',
                fontWeight: 500,
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}>
                {config.label}
              </span>
              <span style={{
                fontSize: '12px',
                color: 'var(--color-accent)',
                fontVariantNumeric: 'tabular-nums',
              }}>
                {value}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
              <span style={{
                fontSize: '11px',
                color: 'var(--color-text-muted)',
                minWidth: '48px',
              }}>
                {config.leftLabel}
              </span>
              <input
                type="range"
                className="evoke-range-input"
                min={0}
                max={100}
                step={1}
                value={value}
                disabled={disabled}
                onChange={(e) => handleChange(config.key, Number(e.target.value))}
                aria-label={config.label}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={value}
                style={{
                  background: `linear-gradient(to right, var(--color-accent) 0%, var(--color-accent) ${value}%, var(--color-border) ${value}%, var(--color-border) 100%)`,
                }}
              />
              <span style={{
                fontSize: '11px',
                color: 'var(--color-text-muted)',
                minWidth: '48px',
                textAlign: 'right',
              }}>
                {config.rightLabel}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
