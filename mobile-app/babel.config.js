module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
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
            '@types': './src/types',
            '@assets': './assets'
          }
        }
      ],
      [
        '@babel/plugin-proposal-export-namespace-from',
        {
          loose: true
        }
      ],
      'react-native-reanimated/plugin'
    ]
  };
};