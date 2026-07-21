// Unit tests for format-report.js — run with:  node test-format-report.js
// Covers all four alert tiers (INFO / MONITOR / WARNING / CRITICAL) and asserts:
//   1. every original snake_case key is still present and unchanged
//   2. no original key was accidentally renamed (exact top-level key set)
//   3. camelCaseReport exists, is fully camelCase, and creditRating is correct

const assert = require('assert');
const { formatReport, scoreToRating } = require('./format-report');

// The 14 snake_case fields the RiskLog Google Sheet auto-maps to. These must
// never change. The 15th top-level key is the new nested camelCaseReport.
const ORIGINAL_KEYS = [
  'timestamp', 'ticker', 'risk_score', 'alert_level', 'current_price',
  'position_value', 'unrealized_pl', 'risk_factors', 'action', 'urgency',
  'position_percent', 'stop_loss_price', 'volatility', 'ai_analysis'
];

const CAMEL_KEYS = [
  'timestamp', 'ticker', 'riskScore', 'alertLevel', 'currentPrice',
  'positionValue', 'unrealizedPl', 'riskFactors', 'action', 'urgency',
  'positionPercent', 'stopLossPrice', 'volatility', 'aiAnalysis', 'creditRating'
];

// snake -> camel mapping so we can assert the mirrored values are identical.
const FIELD_MAP = {
  timestamp: 'timestamp',
  ticker: 'ticker',
  risk_score: 'riskScore',
  alert_level: 'alertLevel',
  current_price: 'currentPrice',
  position_value: 'positionValue',
  unrealized_pl: 'unrealizedPl',
  risk_factors: 'riskFactors',
  action: 'action',
  urgency: 'urgency',
  position_percent: 'positionPercent',
  stop_loss_price: 'stopLossPrice',
  volatility: 'volatility',
  ai_analysis: 'aiAnalysis'
};

const CAMEL_RE = /^[a-z][a-zA-Z0-9]*$/; // lowercase first char, no underscores

function makeInputs(riskScore) {
  const llmInput = {
    choices: [{ message: { content: `AI analysis for score ${riskScore}` } }]
  };
  const prepareNodeJson = {
    original_data: {
      ticker: 'TEST',
      metrics: {
        current_price: '150.00',
        position_value: '15000.00',
        position_percent: '7.50'
      },
      performance: {
        unrealized_pl: '1200.00',
        volatility: '32.10'
      },
      risk: {
        risk_score: riskScore,
        risk_factors: ['Position oversized', 'Near stop loss'],
        stop_loss_price: '138.00'
      },
      recommendation: {
        action: 'HOLD',
        urgency: 'LOW'
      }
    }
  };
  return { llmInput, prepareNodeJson };
}

// tier -> { riskScore, expectedAlert, expectedRating }
const TIERS = [
  { name: 'INFO',     riskScore: 5,  expectedAlert: 'INFO',     expectedRating: 'AAA' },
  { name: 'MONITOR',  riskScore: 25, expectedAlert: 'MONITOR',  expectedRating: 'A'   },
  { name: 'WARNING',  riskScore: 45, expectedAlert: 'WARNING',  expectedRating: 'BB'  },
  { name: 'CRITICAL', riskScore: 90, expectedAlert: 'CRITICAL', expectedRating: 'CC'  }
];

let passed = 0;

for (const tier of TIERS) {
  const { llmInput, prepareNodeJson } = makeInputs(tier.riskScore);
  const out = formatReport(llmInput, prepareNodeJson);

  // (2) exact top-level key set — proves nothing was renamed and only
  // camelCaseReport was added alongside the originals.
  const topKeys = Object.keys(out).sort();
  const expectedTop = [...ORIGINAL_KEYS, 'camelCaseReport'].sort();
  assert.deepStrictEqual(topKeys, expectedTop,
    `[${tier.name}] top-level keys changed: got ${topKeys.join(',')}`);

  // (1) every original snake_case key present with a defined value.
  for (const k of ORIGINAL_KEYS) {
    assert.ok(Object.prototype.hasOwnProperty.call(out, k),
      `[${tier.name}] missing original key: ${k}`);
    assert.notStrictEqual(out[k], undefined,
      `[${tier.name}] original key undefined: ${k}`);
  }

  // Original values match the source data (unchanged behavior).
  assert.strictEqual(out.ticker, 'TEST');
  assert.strictEqual(out.risk_score, tier.riskScore);
  assert.strictEqual(out.alert_level, tier.expectedAlert,
    `[${tier.name}] alert_level wrong`);
  assert.strictEqual(out.current_price, '150.00');
  assert.strictEqual(out.position_value, '15000.00');
  assert.strictEqual(out.unrealized_pl, '1200.00');
  assert.strictEqual(out.risk_factors, 'Position oversized, Near stop loss');
  assert.strictEqual(out.action, 'HOLD');
  assert.strictEqual(out.urgency, 'LOW');
  assert.strictEqual(out.position_percent, '7.50');
  assert.strictEqual(out.stop_loss_price, '138.00');
  assert.strictEqual(out.volatility, '32.10');
  assert.strictEqual(out.ai_analysis, `AI analysis for score ${tier.riskScore}`);

  // (3a) camelCaseReport exists.
  const camel = out.camelCaseReport;
  assert.ok(camel && typeof camel === 'object',
    `[${tier.name}] camelCaseReport missing`);

  // (3b) exact camelCase key set, and every key IS camelCase (no snake_case).
  const camelKeys = Object.keys(camel).sort();
  assert.deepStrictEqual(camelKeys, [...CAMEL_KEYS].sort(),
    `[${tier.name}] camelCaseReport keys wrong: ${camelKeys.join(',')}`);
  for (const k of camelKeys) {
    assert.ok(CAMEL_RE.test(k),
      `[${tier.name}] key is not camelCase: ${k}`);
  }

  // Mirrored values equal their snake_case counterparts.
  for (const [snake, cc] of Object.entries(FIELD_MAP)) {
    assert.strictEqual(camel[cc], out[snake],
      `[${tier.name}] camel ${cc} != snake ${snake}`);
  }

  // (3c) creditRating correct for this tier.
  assert.strictEqual(camel.creditRating, tier.expectedRating,
    `[${tier.name}] creditRating: expected ${tier.expectedRating}, got ${camel.creditRating}`);

  console.log(`  ok  ${tier.name.padEnd(8)} score=${String(tier.riskScore).padStart(3)}  alert=${out.alert_level.padEnd(8)}  rating=${camel.creditRating}`);
  passed++;
}

// Direct boundary checks for scoreToRating() across the full table.
const RATING_CASES = [
  [0, 'AAA'], [9, 'AAA'], [10, 'AA'], [19, 'AA'], [20, 'A'], [29, 'A'],
  [30, 'BBB'], [39, 'BBB'], [40, 'BB'], [54, 'BB'], [55, 'B'], [69, 'B'],
  [70, 'CCC'], [84, 'CCC'], [85, 'CC'], [99, 'CC'], [100, 'D'], [150, 'D']
];
for (const [score, rating] of RATING_CASES) {
  assert.strictEqual(scoreToRating(score), rating,
    `scoreToRating(${score}) expected ${rating}, got ${scoreToRating(score)}`);
}
console.log(`  ok  scoreToRating boundary table (${RATING_CASES.length} cases)`);

console.log(`\nAll tests passed: ${passed} tiers + boundary table.`);
