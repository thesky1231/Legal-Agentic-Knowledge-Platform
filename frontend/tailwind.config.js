/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        parchment: "#f7f2ea",
        "parchment-deep": "#eee6d8",
        ink: "#201b18",
        muted: "#6d6159",
        forest: "#22382e",
        bronze: "#8f6a4a",
        sage: "#3e5b4c"
      },
      boxShadow: {
        panel: "0 24px 48px rgba(62, 47, 34, 0.12)"
      },
      fontFamily: {
        serifDisplay: ["Songti SC", "STSong", "SimSun", "serif"],
        body: ["Microsoft YaHei", "PingFang SC", "sans-serif"]
      },
      backgroundImage: {
        atmosphere:
          "radial-gradient(circle at top left, rgba(143,106,74,0.18), transparent 28%), radial-gradient(circle at top right, rgba(34,56,46,0.12), transparent 24%), linear-gradient(180deg, #faf6ef 0%, #f4ede2 52%, #f8f3eb 100%)"
      }
    }
  },
  plugins: []
};
