/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#071013",
        panel: "#0d1b1e",
        cyanline: "#38d9c7",
        amberline: "#f4c95d",
        dangerline: "#ff5c77",
      },
      boxShadow: {
        glow: "0 0 28px rgba(56, 217, 199, 0.22)",
      },
    },
  },
  plugins: [],
};
