#!/usr/bin/env node

/**
 * Comprehensive Telegram API Test Runner
 * 
 * This script runs all test suites and provides a comprehensive report
 * Usage: node run-all-tests.js [--verbose] [--frontend] [--api] [--backend]
 */

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

class TestRunner {
  constructor() {
    this.results = {
      frontend: { status: 'pending', duration: 0, details: null },
      api: { status: 'pending', duration: 0, details: null },
      backend: { status: 'pending', duration: 0, details: null },
      browser: { status: 'pending', duration: 0, details: null }
    };
    
    this.options = {
      verbose: process.argv.includes('--verbose') || process.argv.includes('-v'),
      frontend: process.argv.includes('--frontend'),
      api: process.argv.includes('--api'),
      backend: process.argv.includes('--backend'),
      browser: process.argv.includes('--browser'),
      all: !process.argv.slice(2).some(arg => ['--frontend', '--api', '--backend', '--browser'].includes(arg))
    };
    
    this.startTime = Date.now();
  }

  log(message, color = 'white') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  logSection(title) {
    console.log(`\n${colors.cyan}${'='.repeat(60)}`);
    console.log(`${colors.bright}${colors.cyan}${title}${colors.reset}`);
    console.log(`${colors.cyan}${'='.repeat(60)}${colors.reset}\n`);
  }

  async runCommand(command, args = [], options = {}) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      if (this.options.verbose) {
        this.log(`Running: ${command} ${args.join(' ')}`, 'blue');
      }
      
      const child = spawn(command, args, {
        stdio: this.options.verbose ? 'inherit' : 'pipe',
        shell: true,
        ...options
      });
      
      let stdout = '';
      let stderr = '';
      
      if (!this.options.verbose) {
        child.stdout?.on('data', (data) => {
          stdout += data.toString();
        });
        
        child.stderr?.on('data', (data) => {
          stderr += data.toString();
        });
      }
      
      child.on('close', (code) => {
        const duration = Date.now() - startTime;
        const result = {
          code,
          duration,
          stdout: stdout.trim(),
          stderr: stderr.trim()
        };
        
        if (code === 0) {
          resolve(result);
        } else {
          reject(result);
        }
      });
      
      child.on('error', (error) => {
        reject({
          code: -1,
          duration: Date.now() - startTime,
          error: error.message,
          stdout: '',
          stderr: ''
        });
      });
    });
  }

  async checkPrerequisites() {
    this.logSection('Checking Prerequisites');
    
    const checks = [
      { name: 'Node.js', command: 'node', args: ['--version'] },
      { name: 'NPM', command: 'npm', args: ['--version'] },
      { name: 'Python', command: 'python', args: ['--version'] }
    ];
    
    for (const check of checks) {
      try {
        const result = await this.runCommand(check.command, check.args);
        this.log(`✓ ${check.name}: Available`, 'green');
        if (this.options.verbose && result.stdout) {
          this.log(`  Version: ${result.stdout}`, 'blue');
        }
      } catch (error) {
        this.log(`✗ ${check.name}: Not available`, 'red');
        if (this.options.verbose && error.stderr) {
          this.log(`  Error: ${error.stderr}`, 'red');
        }
      }
    }
    
    // Check if required files exist
    const requiredFiles = [
      'test-telegram-api.js',
      'telegram-api-tests.js',
      'test_telegram_backend.py'
    ];
    
    this.log('\nChecking test files:', 'yellow');
    for (const file of requiredFiles) {
      if (fs.existsSync(file)) {
        this.log(`✓ ${file}: Found`, 'green');
      } else {
        this.log(`✗ ${file}: Missing`, 'red');
      }
    }
  }

  async runFrontendTests() {
    if (!this.options.all && !this.options.frontend) return;
    
    this.logSection('Running Frontend Tests');
    
    try {
      // Check if we're in the frontend directory or need to navigate to it
      const frontendDir = fs.existsSync('./src') ? '.' : './frontend';
      
      if (!fs.existsSync(path.join(frontendDir, 'package.json'))) {
        throw new Error('Frontend package.json not found');
      }
      
      // Install dependencies if node_modules doesn't exist
      if (!fs.existsSync(path.join(frontendDir, 'node_modules'))) {
        this.log('Installing frontend dependencies...', 'yellow');
        await this.runCommand('npm', ['install'], { cwd: frontendDir });
      }
      
      // Run tests
      const result = await this.runCommand('npm', ['test', '--', '--watchAll=false'], { cwd: frontendDir });
      
      this.results.frontend = {
        status: 'passed',
        duration: result.duration,
        details: result.stdout
      };
      
      this.log('✓ Frontend tests passed', 'green');
      
    } catch (error) {
      this.results.frontend = {
        status: 'failed',
        duration: error.duration || 0,
        details: error.stderr || error.error || 'Unknown error'
      };
      
      this.log('✗ Frontend tests failed', 'red');
      if (this.options.verbose) {
        this.log(error.stderr || error.error || 'No error details', 'red');
      }
    }
  }

  async runAPITests() {
    if (!this.options.all && !this.options.api) return;
    
    this.logSection('Running API Tests');
    
    try {
      const result = await this.runCommand('node', ['test-telegram-api.js']);
      
      this.results.api = {
        status: 'passed',
        duration: result.duration,
        details: result.stdout
      };
      
      this.log('✓ API tests passed', 'green');
      
    } catch (error) {
      this.results.api = {
        status: 'failed',
        duration: error.duration || 0,
        details: error.stderr || error.error || 'Unknown error'
      };
      
      this.log('✗ API tests failed', 'red');
      if (this.options.verbose) {
        this.log(error.stderr || error.error || 'No error details', 'red');
      }
    }
  }

  async runBackendTests() {
    if (!this.options.all && !this.options.backend) return;
    
    this.logSection('Running Backend Tests');
    
    try {
      const result = await this.runCommand('python', ['test_telegram_backend.py']);
      
      this.results.backend = {
        status: 'passed',
        duration: result.duration,
        details: result.stdout
      };
      
      this.log('✓ Backend tests passed', 'green');
      
    } catch (error) {
      this.results.backend = {
        status: 'failed',
        duration: error.duration || 0,
        details: error.stderr || error.error || 'Unknown error'
      };
      
      this.log('✗ Backend tests failed', 'red');
      if (this.options.verbose) {
        this.log(error.stderr || error.error || 'No error details', 'red');
      }
    }
  }

  async runBrowserTests() {
    if (!this.options.all && !this.options.browser) return;
    
    this.logSection('Running Browser Tests');
    
    try {
      const result = await this.runCommand('node', ['telegram-api-tests.js']);
      
      this.results.browser = {
        status: 'passed',
        duration: result.duration,
        details: result.stdout
      };
      
      this.log('✓ Browser tests passed', 'green');
      
    } catch (error) {
      this.results.browser = {
        status: 'failed',
        duration: error.duration || 0,
        details: error.stderr || error.error || 'Unknown error'
      };
      
      this.log('✗ Browser tests failed', 'red');
      if (this.options.verbose) {
        this.log(error.stderr || error.error || 'No error details', 'red');
      }
    }
  }

  generateReport() {
    this.logSection('Test Results Summary');
    
    const totalDuration = Date.now() - this.startTime;
    
    // Calculate stats
    let total = 0;
    let passed = 0;
    let failed = 0;
    
    Object.values(this.results).forEach(result => {
      if (result.status !== 'pending') {
        total++;
        if (result.status === 'passed') passed++;
        if (result.status === 'failed') failed++;
      }
    });
    
    // Display results
    console.log(`${colors.bright}Test Suite Results:${colors.reset}`);
    console.log(`Total Duration: ${Math.round(totalDuration / 1000)}s\n`);
    
    Object.entries(this.results).forEach(([suite, result]) => {
      if (result.status === 'pending') return;
      
      const status = result.status === 'passed' ? 
        `${colors.green}✓ PASSED${colors.reset}` : 
        `${colors.red}✗ FAILED${colors.reset}`;
      
      const duration = `${Math.round(result.duration / 1000)}s`;
      
      console.log(`${suite.toUpperCase().padEnd(12)} ${status} (${duration})`);
      
      if (this.options.verbose && result.details) {
        console.log(`${colors.blue}Details:${colors.reset}`);
        console.log(result.details.split('\n').map(line => `  ${line}`).join('\n'));
        console.log('');
      }
    });
    
    console.log(`\n${colors.bright}Summary:${colors.reset}`);
    console.log(`${colors.green}Passed: ${passed}${colors.reset}`);
    console.log(`${colors.red}Failed: ${failed}${colors.reset}`);
    console.log(`Total: ${total}`);
    
    if (passed === total && total > 0) {
      console.log(`\n${colors.green}${colors.bright}🎉 All tests passed!${colors.reset}`);
      return 0;
    } else if (failed > 0) {
      console.log(`\n${colors.red}${colors.bright}❌ Some tests failed${colors.reset}`);
      return 1;
    } else {
      console.log(`\n${colors.yellow}${colors.bright}⚠️  No tests were run${colors.reset}`);
      return 1;
    }
  }

  async run() {
    console.log(`${colors.bright}${colors.magenta}Telegram API Test Suite${colors.reset}\n`);
    
    try {
      await this.checkPrerequisites();
      
      // Run tests in parallel where possible
      const promises = [];
      
      if (this.options.all || this.options.frontend) {
        promises.push(this.runFrontendTests());
      }
      
      if (this.options.all || this.options.api) {
        promises.push(this.runAPITests());
      }
      
      if (this.options.all || this.options.backend) {
        promises.push(this.runBackendTests());
      }
      
      if (this.options.all || this.options.browser) {
        promises.push(this.runBrowserTests());
      }
      
      // Wait for all tests to complete
      await Promise.allSettled(promises);
      
      // Generate final report
      const exitCode = this.generateReport();
      
      process.exit(exitCode);
      
    } catch (error) {
      this.log(`\n${colors.red}${colors.bright}Fatal error: ${error.message}${colors.reset}`, 'red');
      process.exit(1);
    }
  }
}

// Handle command line help
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
${colors.bright}Telegram API Test Suite${colors.reset}

Usage: node run-all-tests.js [options]

Options:
  --help, -h         Show this help message
  --verbose, -v      Show verbose output
  --frontend         Run only frontend tests
  --api              Run only API tests  
  --backend          Run only backend tests
  --browser          Run only browser tests

Examples:
  node run-all-tests.js                    # Run all tests
  node run-all-tests.js --verbose          # Run all tests with verbose output
  node run-all-tests.js --frontend --api   # Run only frontend and API tests
  node run-all-tests.js --backend -v       # Run only backend tests with verbose output

${colors.yellow}Note: If no specific test suite is specified, all tests will be run.${colors.reset}
`);
  process.exit(0);
}

// Run the test suite
const runner = new TestRunner();
runner.run().catch(error => {
  console.error(`${colors.red}${colors.bright}Unexpected error: ${error.message}${colors.reset}`);
  process.exit(1);
});