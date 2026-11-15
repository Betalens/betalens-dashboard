import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: { dedupe: ['react', 'react-dom', 'react-plotly.js', 'plotly.js-dist-min', 'lucide-react'] },
  build: { outDir: '../dist/experiment-viewer', emptyOutDir: true, chunkSizeWarningLimit: 6000 },
  server: { fs: { allow: ['..'] }, proxy: { '/api': 'http://127.0.0.1:8020' } },
});
