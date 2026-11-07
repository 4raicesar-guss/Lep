import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
                            server: {
                              // Permite que Vite responda a solicitudes desde el túnel de Cloudflare.
                              // Usamos 'true' para permitir cualquier host (ideal para desarrollo local con túneles dinámicos).
                              allowedHosts: true,
                            }
})
