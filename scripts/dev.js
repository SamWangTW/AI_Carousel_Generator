// Starts the FastAPI backend as a background subprocess, then hands the
// terminal to Expo so the QR code renders correctly.
const { spawn } = require('child_process');
const path = require('path');

const root = path.resolve(__dirname, '..');

// ── Backend (background, output piped to stdout/stderr with [API] prefix) ──
const api = spawn(
  'C:/Users/User/AppData/Local/Programs/Python/Python310/python.exe',
  ['-u', '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
  { cwd: path.join(root, 'backend'), shell: false }
);

const cyan = '\x1b[36m';
const reset = '\x1b[0m';

function prefixLines(data, prefix) {
  return data.toString().split('\n')
    .filter(line => line.length > 0)
    .map(line => `${prefix} ${line}`)
    .join('\n') + '\n';
}

api.stdout.on('data', (d) => process.stdout.write(prefixLines(d, `${cyan}[API]${reset}`)));
api.stderr.on('data', (d) => process.stderr.write(prefixLines(d, `${cyan}[API]${reset}`)));
api.on('exit', (code) => console.log(`${cyan}[API]${reset} process exited (${code})`));

// ── Mobile (foreground, inherits terminal so QR code renders) ──
const mobile = spawn('npx', ['expo', 'start'], {
  cwd: path.join(root, 'mobile'),
  stdio: 'inherit',
  shell: true,
});

mobile.on('exit', (code) => {
  api.kill();
  process.exit(code);
});

process.on('SIGINT', () => {
  api.kill();
  mobile.kill();
  process.exit(0);
});
