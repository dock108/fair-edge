#!/usr/bin/env node

/**
 * Design Token Validation Script
 * 
 * This script checks for:
 * 1. Unused tokens in _tokens.css
 * 2. Hard-coded hex colors outside of _tokens.css
 * 3. Hard-coded font sizes outside of _tokens.css
 * 4. Hard-coded spacing values outside of _tokens.css
 */

const fs = require('fs');
const path = require('path');

// File paths
const TOKENS_FILE = path.join(__dirname, '../static/css/_tokens.css');
const CSS_FILES = [
    path.join(__dirname, '../static/css/dashboard.css'),
    // Add more CSS files here as needed
];

// Regular expressions for validation
const HEX_COLOR_REGEX = /#[0-9a-fA-F]{3,6}/g;
const FONT_SIZE_REGEX = /font-size:\s*[0-9]+(\.[0-9]+)?(px|rem|em)/g;
const SPACING_REGEX = /(padding|margin):\s*[0-9]+(\.[0-9]+)?(px|rem|em)/g;
const TOKEN_USAGE_REGEX = /var\(--([^)]+)\)/g;

/**
 * Extract all defined tokens from _tokens.css
 */
function extractDefinedTokens() {
    try {
        const tokensContent = fs.readFileSync(TOKENS_FILE, 'utf8');
        const tokens = new Set();
        
        // Match CSS custom property definitions more precisely
        // Only match lines that start with whitespace, then --, then property name, then colon
        const lines = tokensContent.split('\n');
        for (const line of lines) {
            const match = line.match(/^\s*--([a-zA-Z0-9-]+)\s*:/);
            if (match) {
                tokens.add(match[1].trim());
            }
        }
        
        return tokens;
    } catch (error) {
        console.error(`Error reading tokens file: ${error.message}`);
        return new Set();
    }
}

/**
 * Extract all used tokens from CSS files
 */
function extractUsedTokens() {
    const usedTokens = new Set();
    
    CSS_FILES.forEach(filePath => {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const matches = content.matchAll(TOKEN_USAGE_REGEX);
            
            for (const match of matches) {
                usedTokens.add(match[1].trim());
            }
        } catch (error) {
            console.error(`Error reading CSS file ${filePath}: ${error.message}`);
        }
    });
    
    return usedTokens;
}

/**
 * Find hard-coded values in CSS files
 */
function findHardCodedValues() {
    const violations = [];
    
    CSS_FILES.forEach(filePath => {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const lines = content.split('\n');
            
            lines.forEach((line, index) => {
                const lineNumber = index + 1;
                
                // Check for hex colors
                const hexMatches = line.match(HEX_COLOR_REGEX);
                if (hexMatches) {
                    hexMatches.forEach(hex => {
                        violations.push({
                            file: path.basename(filePath),
                            line: lineNumber,
                            type: 'hex-color',
                            value: hex,
                            content: line.trim()
                        });
                    });
                }
                
                // Check for hard-coded font sizes
                const fontMatches = line.match(FONT_SIZE_REGEX);
                if (fontMatches) {
                    fontMatches.forEach(fontSize => {
                        violations.push({
                            file: path.basename(filePath),
                            line: lineNumber,
                            type: 'font-size',
                            value: fontSize,
                            content: line.trim()
                        });
                    });
                }
                
                // Check for hard-coded spacing
                const spacingMatches = line.match(SPACING_REGEX);
                if (spacingMatches) {
                    spacingMatches.forEach(spacing => {
                        violations.push({
                            file: path.basename(filePath),
                            line: lineNumber,
                            type: 'spacing',
                            value: spacing,
                            content: line.trim()
                        });
                    });
                }
            });
        } catch (error) {
            console.error(`Error reading CSS file ${filePath}: ${error.message}`);
        }
    });
    
    return violations;
}

/**
 * Main validation function
 */
function validateTokens() {
    console.log('🔍 Design Token Validation Report\n');
    
    const definedTokens = extractDefinedTokens();
    const usedTokens = extractUsedTokens();
    const violations = findHardCodedValues();
    
    console.log(`📊 Token Statistics:`);
    console.log(`   • Defined tokens: ${definedTokens.size}`);
    console.log(`   • Used tokens: ${usedTokens.size}`);
    console.log(`   • Hard-coded violations: ${violations.length}\n`);
    
    // Find unused tokens
    const unusedTokens = [...definedTokens].filter(token => !usedTokens.has(token));
    
    if (unusedTokens.length > 0) {
        console.log('⚠️  Unused Tokens:');
        unusedTokens.forEach(token => {
            console.log(`   --${token}`);
        });
        console.log();
    } else {
        console.log('✅ No unused tokens found\n');
    }
    
    // Find tokens used but not defined
    const undefinedTokens = [...usedTokens].filter(token => !definedTokens.has(token));
    
    if (undefinedTokens.length > 0) {
        console.log('❌ Undefined Tokens:');
        undefinedTokens.forEach(token => {
            console.log(`   --${token}`);
        });
        console.log();
    } else {
        console.log('✅ All used tokens are properly defined\n');
    }
    
    // Report hard-coded violations
    if (violations.length > 0) {
        console.log('❌ Hard-coded Value Violations:');
        
        const groupedViolations = violations.reduce((acc, violation) => {
            if (!acc[violation.type]) acc[violation.type] = [];
            acc[violation.type].push(violation);
            return acc;
        }, {});
        
        Object.entries(groupedViolations).forEach(([type, items]) => {
            console.log(`\n   ${type.toUpperCase()}:`);
            items.forEach(item => {
                console.log(`   ${item.file}:${item.line} - ${item.value}`);
                console.log(`     "${item.content}"`);
            });
        });
        console.log();
    } else {
        console.log('✅ No hard-coded values found outside _tokens.css\n');
    }
    
    // Summary
    const hasIssues = unusedTokens.length > 0 || undefinedTokens.length > 0 || violations.length > 0;
    
    if (hasIssues) {
        console.log('❌ Validation failed - Please address the issues above');
        process.exit(1);
    } else {
        console.log('🎉 All validations passed!');
        console.log('   • No unused tokens');
        console.log('   • All tokens properly defined');
        console.log('   • No hard-coded values found');
    }
}

// Run validation
validateTokens(); 