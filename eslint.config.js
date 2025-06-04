module.exports = {
  root: true,
  extends: ['./packages/config/eslint/base.js'],
  ignorePatterns: [
    'node_modules/',
    '.next/',
    'dist/',
    'build/',
    '*.config.js',
    '*.config.ts'
  ]
}; 