const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add support for monorepos and workspaces
config.watchFolders = [__dirname];

// Add support for TypeScript
config.resolver.sourceExts.push('jsx', 'js', 'ts', 'tsx', 'json');

// Add support for watermelondb
config.resolver.alias = {
  '@babel/runtime': '@babel/runtime',
};

module.exports = config;