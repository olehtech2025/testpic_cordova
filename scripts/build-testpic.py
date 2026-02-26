#!/usr/bin/env python3
"""
Generates www/index.html from testpic source for Cordova build.
Transformations:
  1. Copy game-sdk.umd.js
  2. $BACKEND_PUBLICK_SDK_URL → game-sdk.umd.js
  3. $REACT_APP_BACKEND_URL_GAME_CONFIG → https://stage-configs.artintgames.com
  4. Inject Cordova native Google Sign-In override (before </body>)
"""
import os, shutil, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, '..', 'game-core-sdk-frontend', 'public', 'game', 'testpic', 'index.html')
DEST = os.path.join(ROOT, 'www', 'index.html')
STAGE_URL = 'https://stage-configs.artintgames.com'

# --- 1. Copy SDK UMD bundle (prefer game-core-sdk-frontend/public/sdk/1.0.108) ---
sdk_pattern = os.path.join(ROOT, '..', 'game-core-sdk-frontend', 'public', 'sdk', '1.0.108', 'game-sdk.umd.*.js')
sdk_files = sorted(glob.glob(sdk_pattern))
if not sdk_files:
    sdk_pattern2 = os.path.join(ROOT, '..', 'game-core-sdk-frontend', 'public', 'sdk', '**', 'game-sdk.umd.*.js')
    sdk_files = sorted(glob.glob(sdk_pattern2, recursive=True))
if not sdk_files:
    print('ERROR: game-sdk.umd.*.js not found', file=sys.stderr)
    sys.exit(1)
sdk_src = sdk_files[-1]
shutil.copy(sdk_src, os.path.join(ROOT, 'www', 'game-sdk.umd.js'))
print(f'SDK copied: {os.path.relpath(sdk_src, ROOT)} → www/game-sdk.umd.js')

# --- 2. Read source HTML ---
with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# --- 3. Replace template vars ---
html = html.replace('$BACKEND_PUBLICK_SDK_URL', 'game-sdk.umd.js')
html = html.replace('$REACT_APP_BACKEND_URL_GAME_CONFIG', STAGE_URL)
print('Template vars replaced')

# --- 3a. Align SDK init version with bundled SDK ---
if "version: '1.0.109'" in html:
    html = html.replace("version: '1.0.109'", "version: '1.0.108'")
    print('SDK init version patched to 1.0.108')

# --- 3c. Ensure ads config re-apply runs on Cordova too ---
if "if (!window.cordova && typeof APPLOVIN_ADS_CONFIG !== 'undefined' && coreSDK?.ads?.setMockConfig) {" in html:
    html = html.replace(
        "if (!window.cordova && typeof APPLOVIN_ADS_CONFIG !== 'undefined' && coreSDK?.ads?.setMockConfig) {",
        "if (typeof APPLOVIN_ADS_CONFIG !== 'undefined' && coreSDK?.ads?.setMockConfig) {"
    )
    print('Ads re-apply enabled for Cordova')

# --- 3b. Add fallback LEVELS for offline/failed initConfigs ---
import re
start_marker = '// Load LEVELS from remote config via initConfigs'
end_marker = 'let currentLevelIndex = 0;'
if start_marker in html and end_marker in html:
    # Preserve indentation from the marker line
    m = re.search(r'^(\\s*)' + re.escape(start_marker) + r'\\s*$', html, re.M)
    indent = m.group(1) if m else ''
    fallback_block = f"""{indent}// Fallback LEVELS (offline-safe)
{indent}const _itemSvg = (color, label) =>
{indent}    'data:image/svg+xml,' + encodeURIComponent(
{indent}      `<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">` +
{indent}      `<rect width="80" height="80" fill="${{color}}" rx="12"/>` +
{indent}      `<text x="40" y="54" font-size="32" text-anchor="middle" fill="white" font-family="sans-serif">${{label}}</text></svg>`
{indent}    );
{indent}const _bgSvg = (label) =>
{indent}    'data:image/svg+xml,' + encodeURIComponent(
{indent}      `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1536">` +
{indent}      `<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">` +
{indent}      `<stop offset="0%" stop-color="#1a1543"/><stop offset="100%" stop-color="#0a0820"/></linearGradient></defs>` +
{indent}      `<rect width="1024" height="1536" fill="url(#g)"/>` +
{indent}      `<text x="512" y="720" font-size="64" text-anchor="middle" fill="rgba(255,255,255,0.15)" font-family="sans-serif">${{label}}</text>` +
{indent}      `</svg>`
{indent}    );
{indent}const TESTPIC_FALLBACK_LEVELS = [
{indent}    {{ id: 1, key: 'fallback-1', menuTitle: 'Test Level 1', bg: _bgSvg('Level 1'),
{indent}      items: [
{indent}        {{ name: 'Item A', src: _itemSvg('#e74c3c', 'A'), x: 120, y: 200, w: 80, h: 80 }},
{indent}        {{ name: 'Item B', src: _itemSvg('#f39c12', 'B'), x: 600, y: 480, w: 80, h: 80 }},
{indent}        {{ name: 'Item C', src: _itemSvg('#3498db', 'C'), x: 350, y: 900, w: 80, h: 80 }},
{indent}      ]}},
{indent}    {{ id: 2, key: 'fallback-2', menuTitle: 'Test Level 2', bg: _bgSvg('Level 2'),
{indent}      items: [
{indent}        {{ name: 'Item D', src: _itemSvg('#9b59b6', 'D'), x: 200, y: 300,  w: 80, h: 80 }},
{indent}        {{ name: 'Item E', src: _itemSvg('#1abc9c', 'E'), x: 700, y: 700,  w: 80, h: 80 }},
{indent}        {{ name: 'Item F', src: _itemSvg('#2ecc71', 'F'), x: 450, y: 1100, w: 80, h: 80 }},
{indent}      ]}},
{indent}];

{indent}// Load LEVELS from remote config via initConfigs (fallback on failure)
{indent}let LEVELS;
{indent}try {{
{indent}    const configResult = await coreSDK.initConfigs({{
{indent}        version: '2.0.0',
{indent}        keys: ['testpic-init']
{indent}    }});
{indent}    LEVELS = configResult.get('testpic-init.LEVELS') || TESTPIC_FALLBACK_LEVELS;
{indent}    console.log('[GAME] LEVELS from config, count:', LEVELS.length);
{indent}}} catch (e) {{
{indent}    console.error('[GAME] initConfigs failed, using fallback LEVELS:', e && (e.message || e));
{indent}    LEVELS = TESTPIC_FALLBACK_LEVELS;
{indent}}}

{indent}let currentLevelIndex = 0;"""
    start = html.index(start_marker)
    end = html.index(end_marker, start)
    html = html[:start] + fallback_block + html[end + len(end_marker):]
    print('Fallback LEVELS injected (initConfigs guarded)')

# --- 4. Inject Cordova native Google Sign-In override (before </body>) ---
# In Cordova WebView, Google GSI popup is blocked by Google (since 2019).
# Use cordova-plugin-googleplus for native Android Google Sign-In instead.
CORDOVA_GOOGLE_AUTH = '''<script>
(function() {
  if (!window.cordova) return;
  var WEB_CLIENT_ID = '660405658458-a7nlkksb8s2b8341bubgien9ojgei5f9.apps.googleusercontent.com';
  document.addEventListener('deviceready', function() {
    if (!window.plugins || !window.plugins.googleplus) {
      console.warn('[GoogleAuth] cordova-plugin-googleplus not available');
      return;
    }
    if (typeof coreSDK === 'undefined') {
      console.warn('[GoogleAuth] coreSDK not available for Google auth override');
      return;
    }
    coreSDK.getGoogleIdToken = function() {
      return new Promise(function(resolve, reject) {
        window.plugins.googleplus.login(
          { webClientId: WEB_CLIENT_ID, offline: true },
          function(obj) {
            console.log('[GoogleAuth] native login OK:', obj.email);
            resolve({ credential: obj.idToken });
          },
          function(err) {
            console.error('[GoogleAuth] native login failed:', err);
            reject(new Error('Google Sign-In failed: ' + String(err)));
          }
        );
      });
    };
    console.log('[GoogleAuth] Cordova native Google Sign-In override installed');
  }, { once: true });
})();
</script>
</body>'''

if '</body>' in html:
    html = html.replace('</body>', CORDOVA_GOOGLE_AUTH)
    print('Cordova Google Sign-In override injected')
else:
    print('WARNING: </body> not found — Google auth override not injected')

# --- 5. Write output ---
with open(DEST, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Written: www/index.html ({len(html):,} chars)')
