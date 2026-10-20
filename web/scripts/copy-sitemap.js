import fs from 'node:fs';
import path from 'node:path';

const distDir = path.resolve('dist');
const sitemap0 = path.join(distDir, 'sitemap-0.xml');
const sitemapTarget = path.join(distDir, 'sitemap.xml');

if (fs.existsSync(sitemap0)) {
  fs.copyFileSync(sitemap0, sitemapTarget);
  console.log('Successfully generated dist/sitemap.xml from sitemap-0.xml');
} else {
  console.warn('dist/sitemap-0.xml not found to copy');
}
