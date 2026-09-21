module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    // React Native Reanimated plugin - required for animations
    [
      'react-native-reanimated/plugin',
      {
        relativeSourceLocation: true,
      },
    ],

    // Module resolver for absolute imports
    [
      'module-resolver',
      {
        root: ['./src'],
        alias: {
          '@': './src',
          '@components': './src/components',
          '@screens': './src/screens',
          '@services': './src/services',
          '@store': './src/store',
          '@utils': './src/utils',
          '@hooks': './src/hooks',
          '@constants': './src/constants',
          '@types': './src/types',
          '@assets': './src/assets',
          '@navigation': './src/navigation',
        },
        extensions: ['.ios.js', '.android.js', '.js', '.jsx', '.json', '.ts', '.tsx'],
      },
    ],

    // Inline environment variables
    [
      'transform-inline-environment-variables',
      {
        exclude: [
          'NODE_ENV',
          'DEV',
          'BUNDLE',
          'PLATFORM',
          'FLIPPER',
          'HERMES',
          'JSC',
        ],
      },
    ],

    // JSX transform
    [
      '@babel/plugin-transform-react-jsx',
      {
        runtime: 'automatic',
      },
    ],

    // Class properties
    '@babel/plugin-proposal-class-properties',

    // Object rest spread
    '@babel/plugin-proposal-object-rest-spread',

    // Optional chaining
    '@babel/plugin-proposal-optional-chaining',

    // Nullish coalescing
    '@babel/plugin-proposal-nullish-coalescing-operator',

    // Dynamic import
    '@babel/plugin-syntax-dynamic-import',

    // Async generators
    '@babel/plugin-proposal-async-generator-functions',

    // Decorators (for mobx or other decorator-based libraries)
    ['@babel/plugin-proposal-decorators', { legacy: true }],
  ],

  env: {
    production: {
      plugins: [
        // Remove console.log statements in production
        'transform-remove-console',

        // Optimize imports
        'transform-react-remove-prop-types',

        // Minify dead code
        'minify-dead-code-elimination',
      ],
    },
    development: {
      plugins: [
        // Enable react-native-flipper plugin in development
        'react-native-flipper-plugin',
      ],
    },
    test: {
      plugins: [
        // Mock react-native modules for testing
        'react-native-mock-render/plugin',
      ],
    },
  },

  // Ignore certain transforms
  ignore: [
    'node_modules',
    'coverage',
    'build',
    'dist',
  ],
};