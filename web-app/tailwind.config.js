/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'spiral-blue': '#0066CC',
        'spiral-green': '#00CC66',
        'risk-low': '#22C55E',
        'risk-moderate': '#F59E0B',
        'risk-high': '#EF4444',
        'risk-extreme': '#7C2D12',
      },
    },
  },
  plugins: [],
}
