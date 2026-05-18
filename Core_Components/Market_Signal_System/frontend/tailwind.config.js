/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'primary': '#e2e2e2',
        'dim': '#999999',
        'accent': '#7c6dfa',
        'border': '#2a2a2a',
        'background': '#0e0e0e',
      }
    },
  },
  plugins: [],
}