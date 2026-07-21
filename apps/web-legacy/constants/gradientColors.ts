/**
 * AI-inspired gradient color constants for consistent styling across components
 */

// Base color values (RGB)
export const GRADIENT_COLORS = {
  blue: { r: 59, g: 130, b: 246 }, // blue-500
  purple: { r: 147, g: 51, b: 234 }, // purple-600
  pink: { r: 236, g: 72, b: 153 }, // pink-500
  white: { r: 255, g: 255, b: 255 },
  grayLight: { r: 249, g: 250, b: 251 }, // gray-50
} as const;

/**
 * Helper function to create rgba color string
 */
const rgba = (color: { r: number; g: number; b: number }, alpha: number): string => {
  return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
};

/**
 * Border gradient colors - Default state
 */
export const borderGradientDefault = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.blue, 0.3)} 0%,
  ${rgba(GRADIENT_COLORS.purple, 0.3)} 50%,
  ${rgba(GRADIENT_COLORS.blue, 0.3)} 100%
)`;

/**
 * Border gradient colors - Hover state
 */
export const borderGradientHover = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.blue, 0.4)} 0%,
  ${rgba(GRADIENT_COLORS.purple, 0.4)} 50%,
  ${rgba(GRADIENT_COLORS.blue, 0.4)} 100%
)`;

/**
 * Border gradient colors - Focus state
 */
export const borderGradientFocus = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.blue, 0.45)} 0%,
  ${rgba(GRADIENT_COLORS.purple, 0.5)} 30%,
  ${rgba(GRADIENT_COLORS.pink, 0.45)} 60%,
  ${rgba(GRADIENT_COLORS.purple, 0.5)} 100%
)`;

/**
 * Background gradient colors - Default state (light AI gradient)
 */
export const backgroundGradientDefault = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.white, 0.95)} 0%,
  ${rgba(GRADIENT_COLORS.grayLight, 0.98)} 50%,
  ${rgba(GRADIENT_COLORS.white, 0.95)} 100%
)`;

/**
 * Background gradient colors - Hover state
 */
export const backgroundGradientHover = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.white, 0.98)} 0%,
  ${rgba(GRADIENT_COLORS.grayLight, 1)} 50%,
  ${rgba(GRADIENT_COLORS.white, 0.98)} 100%
)`;

/**
 * Background gradient colors - Focus state
 */
export const backgroundGradientFocus = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.white, 1)} 0%,
  ${rgba(GRADIENT_COLORS.grayLight, 1)} 50%,
  ${rgba(GRADIENT_COLORS.white, 1)} 100%
)`;

/**
 * Box shadow values for different states
 */
export const boxShadows = {
  default: `0 2px 8px ${rgba(GRADIENT_COLORS.blue, 0.08)},
    0 1px 2px ${rgba(GRADIENT_COLORS.purple, 0.1)}`,
  hover: `0 4px 12px ${rgba(GRADIENT_COLORS.blue, 0.12)},
    0 2px 4px ${rgba(GRADIENT_COLORS.purple, 0.15)}`,
  focus: `0 0 0 3px ${rgba(GRADIENT_COLORS.blue, 0.12)},
    0 6px 12px ${rgba(GRADIENT_COLORS.purple, 0.15)},
    0 3px 6px ${rgba(GRADIENT_COLORS.blue, 0.12)}`,
  focusInset: `inset 0 1px 0 ${rgba(GRADIENT_COLORS.white, 0.9)}`,
} as const;

/**
 * Dropdown item gradient colors
 */
export const dropdownGradientHover = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.purple, 0.08)} 0%,
  ${rgba(GRADIENT_COLORS.blue, 0.08)} 100%
)`;

export const dropdownGradientSelected = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.purple, 0.15)} 0%,
  ${rgba(GRADIENT_COLORS.blue, 0.15)} 100%
)`;

/**
 * AI gradient background - colorful gradient for focus states
 */
export const aiGradientBackground = `linear-gradient(
  135deg,
  ${rgba(GRADIENT_COLORS.blue, 0.08)} 0%,
  ${rgba(GRADIENT_COLORS.purple, 0.12)} 30%,
  ${rgba(GRADIENT_COLORS.pink, 0.08)} 60%,
  ${rgba(GRADIENT_COLORS.purple, 0.12)} 100%
)`;

