/**
 * Test: verify that undici ProxyAgent works as fetch() dispatcher
 * for Baileys media uploads.
 *
 * Run inside the bridge container:
 *   node test-media-proxy.mjs
 *
 * This simulates what Baileys does internally:
 *   fetch(url, { dispatcher: fetchAgent, ... })
 */

import { ProxyAgent } from 'undici';
import { HttpsProxyAgent } from 'https-proxy-agent';

const proxyUrl =
  process.env.HTTPS_PROXY || process.env.HTTP_PROXY ||
  process.env.https_proxy || process.env.http_proxy;

if (!proxyUrl) {
  console.error('No proxy env var set. Set HTTPS_PROXY or HTTP_PROXY.');
  process.exit(1);
}

console.log(`Proxy: ${proxyUrl.replace(/:[^:@]*@/, ':***@')}\n`);

// WhatsApp media upload hosts (same ones Baileys tries)
const WA_HOSTS = [
  'mmg.whatsapp.net',
  'media.fmed1-2.fna.whatsapp.net',
];

const testUrl = `https://${WA_HOSTS[0]}/`;

// ── Test 1: undici ProxyAgent as dispatcher (NEW - correct approach) ──
console.log('TEST 1: fetch() + undici ProxyAgent dispatcher');
try {
  const agent = new ProxyAgent(proxyUrl);
  const res = await fetch(testUrl, {
    dispatcher: agent,
    method: 'GET',
    signal: AbortSignal.timeout(15000),
  });
  // We expect 4xx/5xx since we're not sending valid auth, but a response
  // means the proxy + TLS connection works.
  console.log(`  Status: ${res.status} ${res.statusText}`);
  console.log('  PASS - undici ProxyAgent works as fetch dispatcher\n');
} catch (err) {
  if (err.cause?.code === 'ECONNREFUSED' || err.cause?.code === 'ENOTFOUND') {
    console.log(`  FAIL - proxy unreachable: ${err.cause.code}\n`);
  } else if (err.name === 'TimeoutError') {
    console.log('  FAIL - timed out (proxy or host unreachable)\n');
  } else {
    console.log(`  FAIL - ${err.message}\n`);
  }
}

// ── Test 2: HttpsProxyAgent as dispatcher (OLD - broken approach) ──
console.log('TEST 2: fetch() + HttpsProxyAgent dispatcher (old broken way)');
try {
  const agent = new HttpsProxyAgent(proxyUrl);
  const res = await fetch(testUrl, {
    dispatcher: agent,   // wrong type! should be ignored/error
    method: 'GET',
    signal: AbortSignal.timeout(15000),
  });
  console.log(`  Status: ${res.status} ${res.statusText}`);
  console.log('  Got response (global dispatcher may have caught it)\n');
} catch (err) {
  if (err.name === 'TimeoutError') {
    console.log('  EXPECTED FAIL - timed out (HttpsProxyAgent ignored as dispatcher)\n');
  } else {
    console.log(`  EXPECTED FAIL - ${err.message}\n`);
  }
}

// ── Test 3: fetch() with NO dispatcher and NO global proxy ──
console.log('TEST 3: fetch() with no dispatcher (direct, no proxy)');
try {
  const res = await fetch(testUrl, {
    method: 'GET',
    signal: AbortSignal.timeout(10000),
  });
  console.log(`  Status: ${res.status} ${res.statusText}`);
  console.log('  Connected directly (may mean proxy is not needed or global dispatcher is set)\n');
} catch (err) {
  if (err.name === 'TimeoutError') {
    console.log('  Timed out - direct connection blocked (proxy IS needed)\n');
  } else {
    console.log(`  ${err.message}\n`);
  }
}

console.log('Done. If TEST 1 shows PASS, the fix is working.');
