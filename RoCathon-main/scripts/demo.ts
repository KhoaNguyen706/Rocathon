import * as dotenv from 'dotenv';
dotenv.config();

import * as fs from 'fs';
import * as path from 'path';
import { searchCreators } from '../src/searchCreators';
import type { BrandProfile } from '../src/types';

const brandSmartHome: BrandProfile = {
  id: 'brand_smart_home',
  industries: ['Home'],
  target_audience: { gender: 'FEMALE', age_ranges: ['25-34'] },
  gmv: 50000,
};

const brandFitness: BrandProfile = {
  id: 'brand_fitness',
  industries: ['Sports & Outdoors', 'Health'],
  target_audience: { gender: 'MALE', age_ranges: ['18-24', '25-34'] },
  gmv: 80000,
};

const brandBeauty: BrandProfile = {
  id: 'brand_beauty',
  industries: ['Beauty', 'Health'],
  target_audience: { gender: 'FEMALE', age_ranges: ['25-34', '35-44'] },
  gmv: 120000,
};

interface DemoScenario {
  query: string;
  brand: BrandProfile;
}

const scenarios: DemoScenario[] = [
  { query: 'Affordable home decor for small apartments', brand: brandSmartHome },
  { query: 'High-energy fitness content for young men', brand: brandFitness },
  { query: 'Gentle skincare routines for sensitive skin', brand: brandBeauty },
];

function printResults(query: string, brandId: string, top10: any[]) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`Query:   "${query}"`);
  console.log(`Brand:   ${brandId}`);
  console.log('='.repeat(70));

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
}

async function main() {
  const outputDir = path.resolve(__dirname, '..', 'output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const allResults: Record<string, any> = {};

  for (const scenario of scenarios) {
    const results = await searchCreators(scenario.query, scenario.brand);
    const top10 = results.slice(0, 10);

    printResults(scenario.query, scenario.brand.id, top10);

    allResults[scenario.brand.id] = {
      query: scenario.query,
      brand: scenario.brand,
      top_10: top10,
    };
  }

  const resultsPath = path.join(outputDir, 'results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(allResults, null, 2));
  console.log(`\nAll results saved to ${resultsPath}`);

  const submissionTop10 = allResults['brand_smart_home'].top_10;
  const submissionPath = path.join(outputDir, 'submission.json');
  fs.writeFileSync(submissionPath, JSON.stringify(submissionTop10, null, 2));
  console.log(`Submission file saved to ${submissionPath}`);
}

main().catch((err) => {
  console.error('Demo failed:', err);
  process.exit(1);
});
