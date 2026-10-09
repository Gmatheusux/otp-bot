/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          950: '#0b0c0e',
          900: '#121316',
          850: '#17181c',
          800: '#1d1f24',
          700: '#2a2d33',
          600: '#3a3d45',
          500: '#5b5f68',
          400: '#8b8f98',
          300: '#b4b7bf',
          200: '#d6d8dd',
          100: '#eceef1',
        },
        accent: {
          600: '#b4571f',
          500: '#c66a30',
          400: '#d98a54',
          300: '#e6ad84',
        },
        hp: '#b14b4b',
        mana: '#3f6fa3',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -8px rgba(0,0,0,0.5)',
      },
    },
  },
  plugins: [],
}
