const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

/**
 * Metro configuration for React Native
 * https://facebook.github.io/metro/docs/configuration
 *
 * @type {import('metro-config').MetroConfig}
 */
const config = {
  // Enable watchman for faster file watching
  watchFolders: [
    // Add any additional watch folders here
  ],

  // Resolver configuration
  resolver: {
    // Alias for easier imports
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

    // File extensions that Metro should resolve
    extensions: [
      'ios.js',
      'android.js',
      'js',
      'jsx',
      'json',
      'ts',
      'tsx',
      'mjs',
    ],

    // Platforms to support
    platforms: ['ios', 'android', 'native'],
  },

  // Transformer configuration
  transformer: {
    // Enable Babel transformer
    babelTransformerPath: require.resolve('metro-react-native-babel-transformer'),

    // Custom configuration for react-native-reanimated
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),

    // Enable minification in production
    minifierConfig: {
      keep_fnames: true,
      mangle: {
        keep_fnames: true,
      },
      output: {
        comments: false,
        ascii_only: true,
      },
    },
  },

  // Server configuration
  server: {
    // Enable HTTPS in development
    https: false,

    // Port for Metro bundler
    port: 8081,

    // Enable source maps in development
    enableSourceMaps: true,
  },

  // Module configuration
  maxWorkers: 4,

  // Cache configuration
  cacheStores: [
    // Use default cache stores
  ],

  // Asset configuration
  assetExts: [
    // Image formats
    'bmp',
    'gif',
    'jpg',
    'jpeg',
    'png',
    'psd',
    'svg',
    'tiff',
    'webp',
    'ico',

    // Font formats
    'ttf',
    'otf',
    'ttc',
    'eot',
    'woff',
    'woff2',

    // Audio formats
    'mp3',
    'wav',
    'ogg',
    'aac',
    'flac',

    // Video formats
    'mp4',
    'mov',
    'avi',
    'wmv',
    'flv',
    'webm',

    // Document formats
    'pdf',
    'doc',
    'docx',
    'xls',
    'xlsx',
    'ppt',
    'pptx',

    // Other formats
    'json',
    'txt',
    'md',
  ],

  // Source file extensions
  sourceExts: [
    'js',
    'jsx',
    'json',
    'ts',
    'tsx',
    'mjs',
  ],

  // Platform extensions
  platformExts: [
    'ios',
    'android',
    'native',
  ],

  // Configuration for react-native-vector-icons
  assetPlugins: [
    'react-native-vector-icons/asset-plugin',
  ],

  // Custom watchman settings for better performance
  watchman: {
    enableSymlinks: true,
  },

  // Node modules configuration
  nodeModules: {
    // Exclude certain node modules from processing
    exclude: [
      /node_modules\/.*\/node_modules/,
    ],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);