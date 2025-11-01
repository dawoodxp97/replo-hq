import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const clubClassNames = (...inputs: ClassValue[]) => {
  return twMerge(clsx(inputs));
}


export const Constants = {
    SETTING_TABS_IDS: {
        PROFILE: "1",
        NOTIFICATIONS: "2",
        APPEARANCE: "3",
        LEARNING: "4",
        SECURITY: "5",
    } 
}