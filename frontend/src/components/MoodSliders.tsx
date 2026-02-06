import { Box, Text, Slider, Flex } from 'gestalt';
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
  const handleChange = (key: keyof MoodSlidersType) => (value: number) => {
    onChange({
      ...sliders,
      [key]: value / 100,
    });
  };

  return (
    <Box padding={4}>
      <Box marginBottom={4}>
        <Text size="400" weight="bold">
          Adjust Mood
        </Text>
      </Box>

      <Flex direction="column" gap={6}>
        {sliderConfigs.map((config) => (
          <Box key={config.key}>
            <Box marginBottom={2}>
              <Text size="200" weight="bold">
                {config.label}
              </Text>
            </Box>
            <Flex alignItems="center" gap={3}>
              <Text size="100" color="subtle">
                {config.leftLabel}
              </Text>
              <Box flex="grow">
                <Slider
                  value={Math.round(sliders[config.key] * 100)}
                  onChange={({ value }) => handleChange(config.key)(value)}
                  min={0}
                  max={100}
                  step={1}
                  disabled={disabled}
                />
              </Box>
              <Text size="100" color="subtle">
                {config.rightLabel}
              </Text>
            </Flex>
          </Box>
        ))}
      </Flex>
    </Box>
  );
}
