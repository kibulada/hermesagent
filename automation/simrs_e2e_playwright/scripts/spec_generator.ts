/**
 * spec_generator.ts — generate Playwright spec skeleton dari AC.
 * Sesuai AGENTS.md §9.2 [2].
 *
 * Usage:
 *   ts-node scripts/spec_generator.ts --id 7434 --slug "fix-menu-perawat" --ac-file <path>
 *   ts-node scripts/spec_generator.ts --id 7434 --slug "fix-menu-perawat" --ac-stdin < ac.txt
 *
 * Output:
 *   specs/generated/wp-<id>-<slug>.spec.ts
 */
import * as fs from 'fs';
import * as path from 'path';

interface Args {
  id: number;
  slug: string;
  ac: string;
  outDir: string;
}

function parseArgs(): Args {
  const argv = process.argv.slice(2);
  const get = (k: string): string | undefined => {
    const i = argv.indexOf(`--${k}`);
    return i >= 0 ? argv[i + 1] : undefined;
  };

  const id = parseInt(get('id') ?? '', 10);
  const slug = get('slug');
  if (!id || !slug) {
    console.error('Usage: --id <id> --slug <slug> [--ac-file <path>|--ac-stdin] [--out-dir <path>]');
    process.exit(1);
  }

  const acFile = get('ac-file');
  const acStdin = argv.includes('--ac-stdin');
  let ac = '';
  if (acFile) {
    ac = fs.readFileSync(acFile, 'utf-8');
  } else if (acStdin) {
    ac = fs.readFileSync(0, 'utf-8');
  } else {
    console.error('Butuh --ac-file atau --ac-stdin');
    process.exit(1);
  }

  return {
    id,
    slug,
    ac,
    outDir: path.resolve(get('out-dir') ?? path.join(__dirname, '..', 'specs', 'generated')),
  };
}

function escapeTemplate(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}

function renderTemplate(args: Args): string {
  const acEscaped = escapeTemplate(args.ac.trim());
  const fileName = `wp-${args.id}-${args.slug}.spec.ts`;
  const specPath = path.join(args.outDir, fileName);

  return `/**
 * SKELETON — dihasilkan spec_generator.ts untuk PP#${args.id}.
 *
 * File ini SENGAJA GAGAL. Generator ini hanya menyalin AC ke dalam komentar;
 * ia tidak bisa menurunkan assertion dari AC. Versi sebelumnya memancarkan
 * \`expect(page).toHaveURL(/doctorDashboard/)\` sebagai "placeholder", yang lulus
 * untuk AC apa pun selama login berhasil — lalu pipeline melaporkan PASS ke tiket.
 * Itu laporan hijau palsu, kerusakan paling mahal yang bisa dilakukan QA.
 *
 * Cara memakainya: terjemahkan AC di bawah jadi assertion nyata lewat subagent
 * \`qa-automation\` (lihat .claude/agents/qa-automation.md), yang wajib lolos gate:
 *   1. tiap assertion menyebut AC asalnya  // AC<n>
 *   2. tiap selector terbukti ada di sourcecode/kesia-fe
 *   3. tiap assertion negatif didahului kontrol positif
 */
import { test, expect } from '@playwright/test';
import { loginAsTimMedinesia } from '../../utils/loginUtils';

test.describe('PP#${args.id} — ${args.slug}', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTimMedinesia(page);
  });

  test('SKELETON — AC belum diterjemahkan jadi assertion', async () => {
    // AC dari tiket:
    // ${acEscaped.split('\n').join('\n    // ')}

    throw new Error(
      'PP#${args.id}: spec masih skeleton. AC belum diterjemahkan jadi assertion. ' +
      'Jalankan subagent qa-automation, jangan laporkan PASS dari file ini.'
    );
  });
});
`;
}

function main(): void {
  const args = parseArgs();
  if (!fs.existsSync(args.outDir)) {
    fs.mkdirSync(args.outDir, { recursive: true });
  }

  const fileName = `wp-${args.id}-${args.slug}.spec.ts`;
  const specPath = path.join(args.outDir, fileName);

  if (fs.existsSync(specPath)) {
    console.error(`${fileName} already exists. Hapus dulu atau pakai slug lain.`);
    process.exit(1);
  }

  fs.writeFileSync(specPath, renderTemplate(args), 'utf-8');
  console.log(specPath);
}

main();
