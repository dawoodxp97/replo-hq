// Tailwind v4 config: enable class-based dark mode so `dark:` responds to `html.dark`
export default {
  darkMode: "class",
  theme: {
    extend: {
      // AI gradient color palette
      colors: {
        'ai-indigo': '#6366f1',
        'ai-purple': '#8b5cf6',
        'ai-cyan': '#06b6d4',
      },
      // Custom gradient utilities
      backgroundImage: {
        'ai-gradient': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)',
        'ai-gradient-soft': 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 50%, rgba(6, 182, 212, 0.1) 100%)',
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(20px, -30px) scale(1.1)" },
          "66%": { transform: "translate(-20px, 20px) scale(0.9)" },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ai': {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.7', transform: 'scale(1.1)' },
        },
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "float-delay-1": "float 8s ease-in-out infinite 2.5s",
        "float-delay-2": "float 8s ease-in-out infinite 5s",
        'fade-up': 'fade-up 0.6s ease-out',
        'pulse-ai': 'pulse-ai 2s ease-in-out infinite',
      },
      // Glassmorphism utilities
      backdropBlur: {
        xs: '2px',
      },
    },
  },
};