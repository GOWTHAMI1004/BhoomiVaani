/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
          950: '#0F3826',
        },
        ivory: {
          DEFAULT: '#FDFBF7',
          light: '#FFFFFF',
          dark: '#F5F1E8',
          border: '#E8E1D3'
        },
        gold: {
          light: '#FDE68A',
          DEFAULT: '#D97706',
          dark: '#B45309',
          accent: '#F59E0B'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'],
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(15, 56, 38, 0.06), 0 2px 6px -1px rgba(15, 56, 38, 0.04)',
        'elevated': '0 10px 30px -4px rgba(15, 56, 38, 0.12), 0 4px 12px -2px rgba(15, 56, 38, 0.08)',
        'gold-glow': '0 0 15px rgba(217, 119, 6, 0.35)',
        'forest-glow': '0 0 20px rgba(15, 56, 38, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ripple': 'ripple 1.5s ease-out infinite',
      },
      keyframes: {
        ripple: {
          '0%': { transform: 'scale(0.8)', opacity: '1' },
          '100%': { transform: 'scale(2.2)', opacity: '0' },
        }
      }
    },
  },
  plugins: [],
}
