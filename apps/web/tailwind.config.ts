import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors
        brand: {
          blue: {
            900: "#1e3f73",
            600: "#2c5aa0", 
            400: "#3d6db0",
          },
          green: {
            900: "#0f2922",
            600: "#1d4e3f",
            400: "#2e6b5a",
          }
        },
        // EV classification colors
        ev: {
          excellent: "#0f7b0f",
          "excellent-bg": "#e8f5e8",
          "excellent-border": "#4caf50",
          high: "#2e7d32",
          "high-bg": "#f1f8e9", 
          "high-border": "#66bb6a",
          positive: "#f57c00",
          "positive-bg": "#fff8e1",
          "positive-border": "#ffb74d",
          neutral: "#424242",
          "neutral-bg": "#f5f5f5",
          "neutral-border": "#9e9e9e",
          negative: "#c62828",
          "negative-bg": "#ffebee",
          "negative-border": "#ef5350",
        },
        // System status colors
        success: "#2e7d32",
        warning: "#f57c00",
        error: "#c62828",
        info: "#2c5aa0",
        // Surfaces
        surface: {
          0: "#ffffff",
          1: "#f5f7fb", 
          2: "#f8f9fa",
          3: "#e9ecef",
        },
        // Text colors
        text: {
          primary: "#000000",
          secondary: "#1a1a1a",
          muted: "#333333",
          inverse: "#ffffff",
          disabled: "#6c757d",
        },
        // Borders
        border: {
          primary: "#e0e0e0",
          light: "#eeeeee",
          focus: "#2c5aa0",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Monaco", "Consolas", "monospace"],
      },
      spacing: {
        "sp-1": "0.25rem",  // 4px
        "sp-2": "0.5rem",   // 8px  
        "sp-3": "0.75rem",  // 12px
        "sp-4": "1rem",     // 16px
        "sp-5": "1.25rem",  // 20px
        "sp-6": "1.5rem",   // 24px
        "sp-8": "2rem",     // 32px
        "sp-10": "2.5rem",  // 40px
        "sp-12": "3rem",    // 48px
        "sp-16": "4rem",    // 64px
        "sp-20": "5rem",    // 80px
      },
      borderRadius: {
        's': '4px',
        'm': '8px', 
        'l': '12px',
        'xl': '16px',
      },
      boxShadow: {
        's': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'm': '0 4px 8px rgba(0, 0, 0, 0.08)',
        'l': '0 8px 16px rgba(0, 0, 0, 0.12)',
        'xl': '0 12px 32px rgba(0, 0, 0, 0.16)',
        'focus': '0 0 0 2px rgba(44, 90, 160, 0.25)',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-up': 'slideUp 300ms ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config; 