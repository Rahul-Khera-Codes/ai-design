/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        amber: {
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        background: '#02040a',
        surface: '#050816',
      },
      boxShadow: {
        'amber-glow': '0 0 40px rgba(245, 158, 11, 0.55)',
      },
    },
  },
  plugins: [],
}
