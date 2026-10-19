/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a'
        },
        accent: {
          500: '#10b981',
          600: '#059669'
        }
      },
      fontFamily: {
        sans: ['Cairo', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Tajawal', 'Cairo', 'sans-serif']
      }
    },
  },
  plugins: [],
}
