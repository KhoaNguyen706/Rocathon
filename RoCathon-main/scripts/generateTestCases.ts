import * as dotenv from 'dotenv';
dotenv.config();

import * as fs from 'fs';
import * as path from 'path';
import { searchCreators } from '../src/searchCreators';
import type { BrandProfile } from '../src/types';

const testCases = [
  {
    name: 'chaotic_mom_cleaning',
    query: 'chaotic mom blogger who reviews effective cleaning products',
    brand: {
      id: 'brand_smart_home',
      industries: ['Home'] as any,
      target_audience: { gender: 'FEMALE' as const, age_ranges: ['25-34'] },
      gmv: 50000,
    },
  },
  {
    name: 'tech_gadgets_students',
    query: 'tech gadgets and phone accessories for college students',
    brand: {
      id: 'brand_fitness',
      industries: ['Sports & Outdoors', 'Health'] as any,
      target_audience: { gender: 'MALE' as const, age_ranges: ['18-24', '25-34'] },
      gmv: 80000,
    },
  },
  {
    name: 'luxury_anti_aging',
    query: 'luxury anti-aging skincare for women over 40',
    brand: {
      id: 'brand_beauty',
      industries: ['Beauty', 'Health'] as any,
      target_audience: { gender: 'FEMALE' as const, age_ranges: ['35-44', '45-54'] },
      gmv: 120000,
    },
  },
  {
    name: 'pet_nutrition',
    query: 'organic pet food and nutrition tips for dog owners',
    brand: {
      id: 'brand_pet',
      industries: ['Pet'] as any,
      target_audience: { gender: 'FEMALE' as const, age_ranges: ['25-34', '35-44'] },
      gmv: 40000,
    },
  },
];

async function main() {
  const outputDir = path.resolve(__dirname, '..', 'output', 'test_cases');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  for (const tc of testCases) {
    console.log(`\nRunning: "${tc.query}" (${tc.brand.id})`);
    const results = await searchCreators(tc.query, tc.brand);
    const top10 = results.slice(0, 10);

    const output = {
      query: tc.query,
      brand: tc.brand,
      top_10: top10,
    };

    const filePath = path.join(outputDir, `${tc.name}.json`);
    fs.writeFileSync(filePath, JSON.stringify(output, null, 2));
    console.log(`  Saved ${top10.length} results to ${filePath}`);

    top10.slice(0, 3).forEach((c, i) => {
      console.log(`  ${i + 1}. @${c.username} | final=${c.scores.final_score}`);
    });
  }

  console.log('\nAll test cases generated.');
}

main().catch((err) => {
  console.error('Failed:', err);
  process.exit(1);
});
