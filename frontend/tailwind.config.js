/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-primary': '#131722',
        'bg-secondary': '#1E222D',
        'bg-tertiary': '#2A2E39',
        'border': '#363A45',
        'text-primary': '#D1D4DC',
        'text-secondary': '#787B86',
        'bull-green': '#26A69A',
        'bear-red': '#EF5350',
        'accent-blue': '#2962FF',
        'accent-gold': '#F7C948',
        'accent-purple': '#9C27B0',
        'success': '#4CAF50',
        'error': '#F44336',
        'warning': '#FF9800',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
