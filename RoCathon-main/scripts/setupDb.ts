import * as fs from 'fs';
import * as path from 'path';

const sqlPath = path.resolve(__dirname, '..', 'sql', 'setup.sql');
const sql = fs.readFileSync(sqlPath, 'utf-8');

console.log('=== Run this SQL in your Supabase SQL Editor ===\n');
console.log(sql);
console.log('\n=== Copy everything above and paste it into: ===');
console.log('Supabase Dashboard > SQL Editor > New query > Run');
