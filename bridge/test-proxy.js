/**
 * Test script to verify proxy configuration
 * Run with: node test-proxy.js
 */

const { HttpsProxyAgent } = require('https-proxy-agent');
const https = require('https');

const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY ||
                 process.env.http_proxy || process.env.HTTP_PROXY ||
                 process.env.all_proxy || process.env.ALL_PROXY;

console.log('Environment variables:');
console.log('  https_proxy =', process.env.https_proxy);
console.log('  HTTPS_PROXY =', process.env.HTTPS_PROXY);
console.log('  http_proxy =', process.env.http_proxy);
console.log('  HTTP_PROXY =', process.env.HTTP_PROXY);
console.log('  all_proxy =', process.env.all_proxy);
console.log('  ALL_PROXY =', process.env.ALL_PROXY);
console.log('');
console.log('Detected proxy URL:', proxyUrl);

if (!proxyUrl) {
  console.log('❌ No proxy configured. Set https_proxy environment variable.');
  process.exit(1);
}

console.log('Creating HTTPS proxy agent...');
const agent = new HttpsProxyAgent(proxyUrl);

console.log('Testing proxy connection to WhatsApp servers...');
const options = {
  hostname: 'web.whatsapp.com',
  port: 443,
  path: '/',
  method: 'GET',
  agent: agent,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  }
};

const req = https.request(options, (res) => {
  console.log('✅ Proxy connection successful!');
  console.log('  Status:', res.statusCode);
  console.log('  Headers:', res.headers);
  process.exit(0);
});

req.on('error', (error) => {
  console.error('❌ Proxy connection failed:', error.message);
  console.error('Full error:', error);
  process.exit(1);
});

req.setTimeout(10000, () => {
  console.error('❌ Connection timeout (10s)');
  req.destroy();
  process.exit(1);
});

req.end();
