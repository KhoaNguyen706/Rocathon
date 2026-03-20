import * as dotenv from 'dotenv';
dotenv.config();

import { searchCreators } from '../src/searchCreators';
import type { BrandProfile } from '../src/types';

const brands: Record<string, BrandProfile> = {
  brand_smart_home: {
    id: 'brand_smart_home',
    industries: ['Home'],
    target_audience: { gender: 'FEMALE', age_ranges: ['25-34'] },
    gmv: 50000,
  },
  brand_fitness: {
    id: 'brand_fitness',
    industries: ['Sports & Outdoors', 'Health'],
    target_audience: { gender: 'MALE', age_ranges: ['18-24', '25-34'] },
    gmv: 80000,
  },
  brand_beauty: {
    id: 'brand_beauty',
    industries: ['Beauty', 'Health'],
    target_audience: { gender: 'FEMALE', age_ranges: ['25-34', '35-44'] },
    gmv: 120000,
  },
};

async function main() {
  const query = process.argv[2];
  const brandId = process.argv[3] || 'brand_smart_home';

  if (!query) {
    console.log('Usage:  npm run search -- "your query here" [brand_id]');
    console.log('');
    console.log('Brands: brand_smart_home (default), brand_fitness, brand_beauty');
    console.log('');
    console.log('Examples:');
    console.log('  npm run search -- "Affordable home decor for small apartments"');
    console.log('  npm run search -- "High-energy fitness content" brand_fitness');
    console.log('  npm run search -- "Gentle skincare routines" brand_beauty');
    process.exit(0);
  }

  const brand = brands[brandId];
  if (!brand) {
    console.error(`Unknown brand: "${brandId}". Use: ${Object.keys(brands).join(', ')}`);
    process.exit(1);
  }

  console.log(`\nQuery:  "${query}"`);
  console.log(`Brand:  ${brandId}`);
  console.log('='.repeat(70));

  const results = await searchCreators(query, brand);
  const top10 = results.slice(0, 10);

  top10.forEach((c, i) => {
    console.log(
      `  ${i + 1}. @${c.username}  |  ` +
        `semantic=${c.scores.semantic_score}  ` +
        `projected=${c.scores.projected_score}  ` +
        `final=${c.scores.final_score}`
    );
    console.log(`     "${c.bio}"`);
    console.log(`     tags: ${c.content_style_tags.join(', ')}`);
  });

  console.log(`\n${top10.length} results returned.`);
}

main().catch((err) => {
  console.error('Search failed:', err);
  process.exit(1);
});
