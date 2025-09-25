import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // OxiWorld Brand Color Palette
        brand: {
          navy: '#000ABE',
          teal: '#00B38F',
          cyan: '#00B39F',
          'light-cyan': '#578E7',
          'medium-teal': '#42DAD9',
          'medium-blue': '#30B2E',
          'dark-teal': '#208CA2',
          'darker-blue': '#145886',
          'darkest-blue': '#032DA0',
        },
        primary: {
          50: '#e6fffc',
          100: '#b3fff7',
          200: '#80fff1',
          300: '#4dffeb',
          400: '#1affe5',
          500: '#00B39F', // Brand cyan
          600: '#00a090',
          700: '#008d81',
          800: '#007a72',
          900: '#006863',
        },
        secondary: {
          50: '#e6f4ff',
          100: '#b3ddff',
          200: '#80c6ff',
          300: '#4dafff',
          400: '#1a98ff',
          500: '#000ABE', // Brand navy
          600: '#0009ab',
          700: '#000898',
          800: '#000785',
          900: '#000672',
        },
        teal: {
          50: '#e6fffe',
          100: '#b3fffc',
          200: '#80fff9',
          300: '#4dfff7',
          400: '#1afff4',
          500: '#00B38F', // Brand teal
          600: '#00a082',
          700: '#008d75',
          800: '#007a68',
          900: '#00675b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-purple': 'linear-gradient(135deg, rgb(109, 40, 217), rgb(147, 51, 234))',
        'gradient-purple-light': 'linear-gradient(135deg, rgb(245, 243, 255), rgba(168, 85, 247, 0.1))',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-purple': 'pulse-purple 2s infinite',
        'slide-in-up': 'slideInUp 0.6s ease-out',
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};

export default config;