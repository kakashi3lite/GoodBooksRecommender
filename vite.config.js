import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Chain-of-Thought: Resolve paths for seamless component imports
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@types': path.resolve(__dirname, './src/types'),
      '@assets': path.resolve(__dirname, './dashboard/assets'),
      '@styles': path.resolve(__dirname, './dashboard/css')
    }
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true,
    open: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  },

  // Build configuration for production
  build: {
    outDir: 'dist',
    // Chain-of-Thought: no sourcemaps in production — smaller payload, less
    // attack surface. Dev debugging unaffected (sourcemaps are dev-only).
    sourcemap: false,
    minify: 'esbuild',
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          animations: ['framer-motion'],
          ui: ['lucide-react', 'react-hot-toast']
        }
      }
    }
  },

  // Forward-Thinking: Environment variables for different deployment stages
  define: {
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
    __PROD__: JSON.stringify(process.env.NODE_ENV === 'production'),
    __VERSION__: JSON.stringify(process.env.npm_package_version)
  },

  // Memory: Optimize dependencies for faster loading
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'framer-motion'
    ]
  }
})
