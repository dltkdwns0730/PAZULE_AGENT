export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#2D6B66",
                "accent": "#FFB88C",
                "background-light": "#f6f7f7",
                "background-dark": "#151d1c",
                "surface-light": "#ffffff",
                "surface-dark": "#1e2827",
                "card-text": "#377771",

                // Shadcn UI base colors mapping
                "border": "hsl(var(--border))",
                "input": "hsl(var(--input))",
                "ring": "hsl(var(--ring))",
                "background": "hsl(var(--background))",
                "foreground": "hsl(var(--foreground))",

                // Screen 4 (Mission Home) & General Mission Theme
                "toss-teal": "#2D6B66",
                "toss-peach": "#FFB88C",
                "toss-coral": "#FF9D5C",
                "toss-mint": "#4ce0b3",
                "toss-bg": "#f2f4f6",
                "toss-card": "#ffffff",
                "toss-text-main": "#2D6B66",
                "toss-text-sub": "#6b7684",

                // Screen 7 (Scan)
                "scan-primary": "#2D6B66",
                "scan-primary-dark": "#1F5350",
                "scan-accent": "#4ce0b3",
                "scan-bg-light": "#f6f7f7",
                "scan-bg-dark": "#151d1c",
                "scan-surface-light": "#ffffff",
                "scan-surface-dark": "#1e2928",

                // Screen 2 (Mission Result)
                "result-primary": "#2D6B66",
                "result-success": "#4ce0b3",
                "result-coupon-start": "#ffaf87",
                "result-coupon-end": "#ff8e72",
                "result-bg-light": "#f9fafb",
                "result-bg-dark": "#101922",

                // Screen 3 (Photo Submission)
                "brand-primary": "#2D6B66",
                "brand-accent": "#FFB88C",
                "status-success": "#4ce0b3",
                "status-error": "#ed6a5e",
                // reusing background-light/dark from result or generic

                // Screen 6 (Wallet Overview)
                "wallet-primary": "#05ad9c",
                "wallet-shop-text": "#2D6B66",
                // wallet bg matches generic

                // Screen 5 (Admin)
                "admin-primary": "#2D6B66",
                "admin-secondary": "#4ce0b3",
                "admin-bg-light": "#f6f7f7",
                "admin-bg-dark": "#151d1c",
                "admin-neutral-light": "#f1f3f3",
                "admin-neutral-dark": "#2d3837",

                // Home Clean White Theme
                "coral-start": "#FFB88C",
                "coral-end": "#FF9D5C",
                "dark-teal": "#2D6B66",
                "pale-coral": "#fff0ec",
                "light-grey": "#f5f7f9",
                "warm-cream": "#faf9f6",
                "pale-border": "#e5e7eb",
                "active-teal": "#2D6B66",

                // Photo Submission Focus Theme
                "primary-dark": "#1F5350",
                "accent-orange": "#FF9D5C",
                "accent-glow": "#ffaf87",
                "accent-mint": "#4ce0b3",
                "bg-soft": "#f8f9fa",
                "glass-border": "rgba(255, 255, 255, 0.6)",
                "glass-surface": "rgba(255, 255, 255, 0.7)",
            },
            fontFamily: {
                "sans": ["Inter", "sans-serif"],
                "display": ["Plus Jakarta Sans", "sans-serif"],
                "body": ["Plus Jakarta Sans", "sans-serif"],
            },
            boxShadow: {
                'soft': '0 4px 20px rgba(0, 0, 0, 0.03)',
                'card': '0 8px 30px rgba(0, 0, 0, 0.06)',
                'hover': '0 8px 30px rgba(0, 0, 0, 0.08)',
                'glow': '0 0 20px rgba(76, 224, 179, 0.3)',
                'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.05)',
                'inner-glow': 'inset 0 0 40px 0 rgba(255, 175, 135, 0.15)',
                'btn-strong': '0 15px 30px -8px rgba(55, 119, 113, 0.4)'
            },
            backgroundImage: {
                'coupon-gradient': 'linear-gradient(135deg, #ffaf87 0%, #ff8e72 100%)',
            },
            keyframes: {
                'slide-up': {
                    '0%': { transform: 'translateY(100%)' },
                    '100%': { transform: 'translateY(0)' },
                },
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'fade-in-up': {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                'confetti': {
                    '0%': { transform: 'translateY(-10vh) rotate(0deg)', opacity: '1' },
                    '100%': { transform: 'translateY(100vh) rotate(720deg)', opacity: '0' },
                },
                'scale-in': {
                    '0%': { transform: 'scale(0.8)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
                'subtle-pulse': {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.6' },
                },
            },
            animation: {
                'slide-up': 'slide-up 0.3s ease-out',
                'fade-in': 'fade-in 0.3s ease-out',
                'fade-in-up': 'fade-in-up 0.5s ease-out',
                'float': 'float 6s ease-in-out infinite',
                'confetti-slow': 'confetti 4s linear infinite',
                'confetti-medium': 'confetti 3s linear infinite',
                'confetti-fast': 'confetti 2.5s linear infinite',
                'scale-in': 'scale-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
                'subtle-pulse': 'subtle-pulse 3s ease-in-out infinite',
            },
        },
    },
    plugins: [],
}
