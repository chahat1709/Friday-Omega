#!/usr/bin/env node
// F.R.I.D.A.Y. Automated Startup Script
// Launches backend, compiles frontend, and optionally starts Electron

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const launchElectron = args.includes('--electron') || args.includes('-e');
const skipBabel = args.includes('--no-babel');
const port = args.find(a => a.startsWith('--port='))?.split('=')[1] || 8000;

console.log('\n' + '='.repeat(80));
console.log('🚀 F.R.I.D.A.Y. Startup Manager');
console.log('='.repeat(80) + '\n');

// ============================================================================
// STEP 1: BABEL COMPILATION
// ============================================================================

if (!skipBabel) {
  console.log('📦 Step 1: Compiling Frontend Code');
  console.log('-'.repeat(80));

  const babel = spawn('npx', [
    'babel',
    'js',
    '--out-dir',
    'dist',
    '--presets',
    '@babel/preset-env,@babel/preset-react',
    '--quiet'
  ]);

  babel.on('close', (code) => {
    if (code === 0) {
      console.log('✅ Frontend compiled successfully\n');
      startBackend();
    } else {
      console.log('⚠️  Babel compilation had issues (code: ' + code + ')');
      console.log('   Continuing without compilation...\n');
      startBackend();
    }
  });
} else {
  console.log('📦 Step 1: Skipping Babel compilation\n');
  startBackend();
}

// ============================================================================
// STEP 2: START BACKEND
// ============================================================================

function startBackend() {
  console.log('🔌 Step 2: Starting Backend Server (Python)');
  console.log('-'.repeat(80));

  // Launch Python Backend
  const venvPython = path.join(__dirname, '.venv', 'Scripts', 'python.exe');
  const systemPython = 'python';
  const pythonCmd = fs.existsSync(venvPython) ? venvPython : systemPython;

  console.log(`🔌 Step 2: Starting Backend Server (using ${pythonCmd})`);

  const backend = spawn(pythonCmd, ['python_backend/main.py'], {
    env: {
      ...process.env,
      // Pass any needed env vars
      PYTHONUNBUFFERED: "1"
    },
    stdio: 'inherit'
  });

  backend.on('error', (err) => {
    console.error('❌ Backend startup failed:', err.message);
    process.exit(1);
  });

  // Give backend time to start
  setTimeout(() => {
    console.log('\n✅ Backend server started on port ' + port);
    if (launchElectron) {
      startElectron();
    } else {
      printInstructions();
    }
  }, 2000);

  process.on('SIGINT', () => {
    console.log('\n\n⏹️  Shutting down...');
    backend.kill('SIGINT');
    process.exit(0);
  });
}

// ============================================================================
// STEP 3: START ELECTRON (Optional)
// ============================================================================

function startElectron() {
  console.log('\n🖥️  Step 3: Launching Electron Frontend');
  console.log('-'.repeat(80) + '\n');

  const electron = spawn('npx', ['electron', '.'], {
    stdio: 'inherit'
  });

  electron.on('error', (err) => {
    console.error('❌ Electron launch failed:', err.message);
    console.log('   Try starting manually with: npx electron .');
  });

  electron.on('close', () => {
    console.log('\n✅ Electron window closed');
  });
}

// ============================================================================
// INSTRUCTIONS
// ============================================================================

function printInstructions() {
  console.log('\n' + '='.repeat(80));
  console.log('✨ F.R.I.D.A.Y. is ready!');
  console.log('='.repeat(80) + '\n');

  console.log('📡 Access F.R.I.D.A.Y. through:');
  console.log(`   • Web:    http://localhost:${port}`);
  console.log('   • Electron: npx electron .');
  console.log('   • API:    http://localhost:' + port + '/chat\n');

  console.log('🎮 Available Commands:');
  console.log('   • Chat:       Send messages in any language');
  console.log('   • Voice:      Enable microphone for voice input');
  console.log('   • System:     Execute system commands (open, search, etc.)');
  console.log('   • Weather:    Get weather information');
  console.log('   • Time/Date:  Check current time and date\n');

  console.log('📊 API Examples:');
  console.log('   • Get Profile: curl http://localhost:' + port + '/api/profile');
  console.log('   • Chat: curl -X POST http://localhost:' + port + '/chat -d \'{"message":"hello"}\' -H "Content-Type: application/json"\n');

  console.log('🧪 Run Tests:');
  console.log('   • Profile:  node test-profile.js');
  console.log('   • Security: node test-security.js\n');

  console.log('⚡ Keyboard Shortcuts:');
  console.log('   • Ctrl+C  - Stop server');
  console.log('   • Ctrl+T  - Toggle voice mode (in app)');
  console.log('   • Ctrl+L  - Clear chat history\n');

  console.log('💡 Tips:');
  console.log('   • Use "open [app]" to launch applications');
  console.log('   • Use "search [query]" to search Google');
  console.log('   • Use "weather" to get current weather');
  console.log('   • F.R.I.D.A.Y. learns from your interactions!\n');

  console.log('📖 Documentation: open README.md in your editor\n');

  console.log('Press Ctrl+C to stop the server.\n');
}
