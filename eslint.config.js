/**
 * ESLint 9 flat config.
 *
 * Chain-of-Thought: the previous `.eslintrc.json` pinned ESLint 8 and
 * `@typescript-eslint` 6, which blocked every Dependabot bump — the grouped
 * upgrade failed `npm ci` because `eslint-plugin-react-refresh@0.5` requires
 * ESLint ^9. The rule set below is deliberately identical to the old config so
 * the migration changes the toolchain, not the code standards.
 */

import js from '@eslint/js'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import security from 'eslint-plugin-security'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
    {
        // `**/._*` is macOS Apple Double noise. ESLint 8 skipped dotfiles by
        // default; flat config does not, so a macOS checkout would otherwise
        // fail the lint gate with "Invalid character" on binary sidecars.
        ignores: [
            'dist/**',
            'build/**',
            'coverage/**',
            'node_modules/**',
            'functions/**',
            'dashboard/**',
            '**/._*',
            '**/.DS_Store'
        ]
    },
    js.configs.recommended,
    tseslint.configs.recommended,
    {
        files: ['src/**/*.{ts,tsx}'],
        languageOptions: {
            ecmaVersion: 2023,
            sourceType: 'module',
            globals: { ...globals.browser, ...globals.node },
            parserOptions: { ecmaFeatures: { jsx: true } }
        },
        plugins: {
            react,
            'react-hooks': reactHooks,
            'react-refresh': reactRefresh,
            security
        },
        settings: { react: { version: 'detect' } },
        rules: {
            '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-non-null-assertion': 'error',
            'react/react-in-jsx-scope': 'off',
            'react/prop-types': 'off',
            // Hooks rules: the same two rules the old `plugin:react-hooks/recommended`
            // preset applied, declared explicitly so a preset reshuffle cannot
            // silently drop them.
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'warn',
            'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
            // Downgraded to warn: this heuristic flags every safe Record/dictionary
            // access (cache lookups, genre counts). Kept visible but non-blocking.
            'security/detect-object-injection': 'warn',
            'security/detect-non-literal-require': 'error'
        }
    },
    {
        files: ['tests/**/*.{ts,tsx}'],
        languageOptions: {
            ecmaVersion: 2023,
            sourceType: 'module',
            globals: { ...globals.node, ...globals.browser }
        }
    }
)
