/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core_admin/templates/**/*.html",
    "./core_admin/apps/**/*.html",
    "./core_admin/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: '#EA580C',
          'orange-dark': '#C2410C',
          'orange-light': '#FFEDD5',
          dark: '#FFFFFF',
          'light-gray': '#F9FAFB',
          'card-bg': '#FFFFFF',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      animation: {
        'marquee': 'marquee 25s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' }
        }
      }
    },
  },
  plugins: [],
}
