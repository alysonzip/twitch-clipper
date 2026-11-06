/**
 * Release script for Electron Builder
 * Usage: node release.js [patch|minor|major]
 */

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const packageJsonPath = path.join(__dirname, 'package.json')
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'))

function bumpVersion(type) {
  const [major, minor, patch] = packageJson.version.split('.').map(Number)

  switch (type) {
    case 'major':
      return `${major + 1}.0.0`
    case 'minor':
      return `${major}.${minor + 1}.0`
    case 'patch':
    default:
      return `${major}.${minor}.${patch + 1}`
  }
}

function updateVersion(newVersion) {
  packageJson.version = newVersion
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n')
  console.log(`Version updated to ${newVersion}`)
}

function runCommand(cmd, cwd = __dirname) {
  console.log(`Running: ${cmd}`)
  try {
    execSync(cmd, { cwd, stdio: 'inherit', shell: true })
  } catch (error) {
    console.error(`Command failed: ${cmd}`)
    process.exit(1)
  }
}

async function main() {
  const bumpType = process.argv[2] || 'patch'
  const newVersion = bumpVersion(bumpType)

  console.log(`=== Releasing Twitch Clipper v${newVersion} ===`)

  // Update version
  updateVersion(newVersion)

  // Build frontend
  console.log('\n--- Building Frontend ---')
  runCommand('npm run build')

  // Build backend
  console.log('\n--- Building Backend ---')
  runCommand('python build_backend.py', path.join(__dirname, '..', 'backend'))

  // Package with Electron Builder
  console.log('\n--- Packaging with Electron Builder ---')
  runCommand('npm run package')

  // Git commit and tag
  console.log('\n--- Creating Git Tag ---')
  runCommand('git add .')
  runCommand(`git commit -m "chore: release v${newVersion}"`)
  runCommand(`git tag -a v${newVersion} -m "Release v${newVersion}"`)

  console.log(`\n=== Release v${newVersion} Complete ===`)
  console.log(`Installer: dist_electron/Twitch Clipper Setup ${newVersion}.exe`)
  console.log(`\nTo publish:`)
  console.log(`  git push origin main --tags`)
  console.log(`  gh release create v${newVersion} dist_electron/*.exe --title "Twitch Clipper v${newVersion}"`)
}

main().catch(console.error)