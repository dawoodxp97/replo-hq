// Tailwind v4 config: enable class-based dark mode so `dark:` responds to `html.dark`
export default {
  darkMode: "class",
  theme: {
    extend: {
      keyframes: {
        float: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(20px, -30px) scale(1.1)" },
          "66%": { transform: "translate(-20px, 20px) scale(0.9)" },
        },
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "float-delay-1": "float 8s ease-in-out infinite 2.5s",
        "float-delay-2": "float 8s ease-in-out infinite 5s",
      },
    },
  },
};