/**
 * 🧪 Vitest Configuration
 * Chain-of-Thought: jsdom environment for React component tests
 * Memory: Shared setup file for jest-dom matchers
 */
import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
            '@components': path.resolve(__dirname, './src/components'),
            '@hooks': path.resolve(__dirname, './src/hooks'),
            '@utils': path.resolve(__dirname, './src/utils'),
            '@stores': path.resolve(__dirname, './src/stores'),
            '@types': path.resolve(__dirname, './src/types')
        }
    },
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./tests/setup.ts'],
        include: ['tests/**/*.{test,spec}.{ts,tsx}'],
        // macOS Apple Double files (._*) are never valid test files — always exclude
        exclude: [
            'node_modules/**',
            'dist/**',
            '**/._*',
            '**/node_modules/**'
        ]
    }
})
