/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#000000',
        charcoal: '#1f2937',
        muted: '#6b7280',
        line: '#E5E5EA',
        mint: '#FF3B30',
        brand: {
          red: '#FF3B30',
          deep: '#E6352A',
          dark: '#E6352A',
          blue: '#007AFF',
          'blue-dark': '#006EE6',
          green: '#34C759',
          'green-dark': '#2EAE4F',
          black: '#000000',
          soft: '#F2F2F7',
          blush: '#F2F2F7',
          gray: '#F2F2F7',
          'gray-medium': '#E5E5EA',
          'gray-dark': '#D1D1D6',
        },
        success: '#34C759',
        saffron: '#007AFF',
        berry: '#E6352A',
      },
      borderRadius: {
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.25rem',
      },
      fontFamily: {
        sans: [
          'Poppins',
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
      },
      boxShadow: {
        soft: '0 16px 42px rgba(2, 8, 23, 0.08)',
        brand: '0 18px 45px rgba(255, 59, 48, 0.22)',
        glass: '0 10px 30px rgba(2, 8, 23, 0.12)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 280ms ease-out',
        slideUp: 'slideUp 360ms ease-out',
        'pulse-slow': 'pulseSlow 2.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
