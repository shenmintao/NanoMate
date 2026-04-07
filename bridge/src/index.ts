#!/usr/bin/env node
/**
 * nanobot WhatsApp Bridge
 * 
 * This bridge connects WhatsApp Web to nanobot's Python backend
 * via WebSocket. It handles authentication, message forwarding,
 * and reconnection logic.
 * 
 * Usage:
 *   npm run build && npm start
 *   
 * Or with custom settings:
 *   BRIDGE_PORT=3001 AUTH_DIR=~/.nanobot/whatsapp npm start
 */

// Polyfill crypto for Baileys in ESM
import { webcrypto } from 'crypto';
if (!globalThis.crypto) {
  (globalThis as any).crypto = webcrypto;
}

// Configure proxy for ALL HTTP/HTTPS requests:
// 1. undici setGlobalDispatcher → covers global fetch()
// 2. Native http/https globalAgent → covers Baileys media uploads (which use https module directly)
import { ProxyAgent, setGlobalDispatcher } from 'undici';
import https from 'https';
import http from 'http';
import { HttpsProxyAgent } from 'https-proxy-agent';

const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.https_proxy || process.env.http_proxy;
if (proxyUrl) {
  try {
    // Cover global fetch()
    const undiciAgent = new ProxyAgent(proxyUrl);
    setGlobalDispatcher(undiciAgent);

    // Cover native https/http module (used by Baileys media upload)
    const httpsAgent = new HttpsProxyAgent(proxyUrl);
    https.globalAgent = httpsAgent as unknown as https.Agent;
    http.globalAgent = httpsAgent as unknown as http.Agent;

    console.log(`🌐 Global proxy configured (fetch + https): ${proxyUrl.replace(/:[^:@]*@/, ':***@')}`);
  } catch (error) {
    console.error('⚠️  Failed to configure global proxy:', error);
  }
}

import { BridgeServer } from './server.js';
import { homedir } from 'os';
import { join } from 'path';

const PORT = parseInt(process.env.BRIDGE_PORT || '3001', 10);
const AUTH_DIR = process.env.AUTH_DIR || join(homedir(), '.nanobot', 'whatsapp-auth');
const TOKEN = process.env.BRIDGE_TOKEN?.trim();

if (!TOKEN) {
  console.error('BRIDGE_TOKEN is required. Start the bridge via nanobot so it can provision a local secret automatically.');
  process.exit(1);
}

console.log('🐈 nanobot WhatsApp Bridge');
console.log('========================\n');

const server = new BridgeServer(PORT, AUTH_DIR, TOKEN);

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\nShutting down...');
  await server.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await server.stop();
  process.exit(0);
});

// Start the server
server.start().catch((error) => {
  console.error('Failed to start bridge:', error);
  process.exit(1);
});
