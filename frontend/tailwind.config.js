/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './context/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body:    ['DM Sans', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      colors: {
        gold: {
          DEFAULT: '#C9A84C',
          light:   '#E8D5A3',
          dim:     'rgba(201,168,76,0.12)',
        },
      },
    },
  },
  plugins: [],
}
