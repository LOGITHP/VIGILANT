/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vigilant: {
          bg: "#061313",
          surface: "#091c1c",
          card: "#0b1617",
          border: "#163133",
          teal: "#15b89a",
          tealHover: "#129e84",
          glow: "#2dd4bf",
          muted: "#6b8a87",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'card-glow': '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 40px rgba(21, 184, 154, 0.1)',
        'teal-glow': '0 0 20px rgba(21, 184, 154, 0.4)',
        'camera-ambient': '0 30px 60px rgba(0, 0, 0, 0.8), 0 0 80px rgba(21, 184, 154, 0.15)',
      }
    },
  },
  plugins: [],
}

