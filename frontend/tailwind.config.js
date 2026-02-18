/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Totsuki brand colors (warm, food-inspired)
        primary: {
          50: '#fef7ee',
          100: '#fdedd3',
          200: '#fad7a5',
          300: '#f6ba6d',
          400: '#f19332',
          500: '#ee7712',
          600: '#df5c08',
          700: '#b94409',
          800: '#93360f',
          900: '#772f10',
        },
      },
    },
  },
  plugins: [],
}
