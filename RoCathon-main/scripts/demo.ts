import * as dotenv from 'dotenv';
dotenv.config();

import { searchCreators } from '../src/searchCreators';
import pool from '../src/db';
import type { BrandProfile } from '../src/types';

const brandSmartHome: BrandProfile = {
  id: 'brand_smart_home',
  industries: ['Home'],
  target_audience: {
    gender: 'FEMALE',
    age_ranges: ['25-34'],
  },
  gmv: 50000,
};

async function main() {
  const query = 'Affordable home decor for small apartments';

  console.log(`Query:   "${query}"`);
  console.log(`Brand:   ${brandSmartHome.id}`);
  console.log('---');

  const results = await searchCreators(query, brandSmartHome);
  const top10 = results.slice(0, 10);

  console.log(`\nTop ${top10.length} creators:\n`);

  top10.forEach((c, i) => {
    console.log(
      `${i + 1}. @${c.username}  |  ` +
        `semantic=${c.scores.semantic_score}  ` +
        `projected=${c.scores.projected_score}  ` +
        `final=${c.scores.final_score}`
    );
    console.log(`   "${c.bio}"`);
    console.log(`   tags: ${c.content_style_tags.join(', ')}`);
    console.log();
  });

  console.log('\n--- Full JSON output ---\n');
  console.log(JSON.stringify(top10, null, 2));

  await pool.end();
}

main().catch((err) => {
  console.error('Demo failed:', err);
  process.exit(1);
});
