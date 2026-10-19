import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  output: 'static',
  site: 'https://tech-comparisons.pages.dev',
  integrations: [tailwind({
    applyBaseStyles: false
  })],
  build: {
    format: 'directory'
  }
});
