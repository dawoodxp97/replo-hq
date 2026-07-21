import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const clubClassNames = (...inputs: ClassValue[]) => {
  return twMerge(clsx(inputs));
}

/**
 * Converts a snake_case string to camelCase
 * @param str - The snake_case string to convert
 * @returns The camelCase string
 */
const toCamelCase = (str: string): string => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

/**
 * Special key mappings for common cases where camelCase conversion needs custom handling
 */
const KEY_MAPPINGS: Record<string, string> = {
  profile_picture_url: 'profilePic',
};

/**
 * Recursively converts all snake_case keys in an object to camelCase
 * Handles nested objects and arrays
 * Supports custom key mappings for special cases
 * @param obj - The object to convert
 * @returns A new object with camelCase keys
 */
export const snakeToCamel = <T = any>(obj: any): T => {
  if (obj === null || obj === undefined) {
    return obj;
  }

  // Handle arrays
  if (Array.isArray(obj)) {
    return obj.map(item => snakeToCamel(item)) as T;
  }

  // Handle objects
  if (typeof obj === 'object' && obj.constructor === Object) {
    const camelObj: any = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        // Check for custom mapping first, then fall back to camelCase conversion
        const camelKey = KEY_MAPPINGS[key] || toCamelCase(key);
        camelObj[camelKey] = snakeToCamel(obj[key]);
      }
    }
    return camelObj as T;
  }

  // Return primitive values as-is
  return obj as T;
};

export const Constants = {
    SETTING_TABS_IDS: {
        PROFILE: "1",
        NOTIFICATIONS: "2",
        APPEARANCE: "3",
        LEARNING: "4",
        SECURITY: "5",
    } 
}