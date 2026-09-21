module.exports = {
  dependencies: {
    'react-native-vector-icons': {
      platforms: {
        ios: {
          sourceDir: '../node_modules/react-native-vector-icons/Fonts',
          project: 'ios/DMLogn8n.xcodeproj',
        },
      },
    },
    'react-native-camera': {
      platforms: {
        android: {
          sourceDir: '../node_modules/react-native-camera/android',
          packageImportPath: 'import io.lum.reactnativecamera.RNCameraPackage;',
        },
      },
    },
    'react-native-push-notification': {
      platforms: {
        android: {
          sourceDir: '../node_modules/react-native-push-notification/android',
          packageImportPath: 'import com.dieam.reactnativepushnotification.ReactNativePushNotificationPackage;',
        },
      },
    },
    'react-native-maps': {
      platforms: {
        android: {
          sourceDir: '../node_modules/react-native-maps/lib/android',
          packageImportPath: 'import com.airbnb.android.reactmaps.MapsPackage;',
        },
      },
    },
  },

  assets: ['./src/assets/fonts/', './src/assets/images/'],

  // Configuration for React Native 0.60+
  reactNativeVersion: '0.72.6',

  // Project configuration
  project: {
    ios: {},
    android: {},
  },

  // Command to run before building
  prebuild: (prebuildConfig) => {
    // Custom prebuild configuration
    return prebuildConfig;
  },

  // Command to run after building
  postbuild: (buildConfig) => {
    // Custom postbuild configuration
    return buildConfig;
  },

  // Configuration for linking
  platforms: {
    ios: {
      project: './ios/DMLogn8n.xcodeproj',
      sharedLibraries: ['libz', 'c++'],
      libraryFolder: 'Libraries',
    },
    android: {
      sourceDir: '../android',
      packageImportPath: 'import com.dmlogn8n.MainApplication;',
      mainActivityPath: 'MainActivity.java',
    },
  },

  // Custom commands
  commands: {
    // Custom build commands
    'build:ios:simulator': 'cd ios && xcodebuild -workspace DMLogn8n.xcworkspace -scheme DMLogn8n -configuration Debug -destination \'platform=iOS Simulator,name=iPhone 14,OS=latest\' build',
    'build:ios:device': 'cd ios && xcodebuild -workspace DMLogn8n.xcworkspace -scheme DMLogn8n -configuration Release -destination generic/platform=iOS build',
    'build:android:debug': 'cd android && ./gradlew assembleDebug',
    'build:android:release': 'cd android && ./gradlew assembleRelease',

    // Custom run commands
    'run:ios:simulator': 'react-native run-ios --simulator="iPhone 14"',
    'run:ios:device': 'react-native run-ios --device',
    'run:android:debug': 'react-native run-android --variant=debug',
    'run:android:release': 'react-native run-android --variant=release',

    // Test commands
    'test:android:debug': 'detox test --configuration android.emu.debug',
    'test:android:release': 'detox test --configuration android.emu.release',
    'test:ios:simulator': 'detox test --configuration ios.sim.debug',
    'test:ios:simulator:release': 'detox test --configuration ios.sim.release',
  },

  // Health checks
  healthChecks: {
    ios: {
      xcode: {
        version: '>=14.0.0',
      },
      cocoapods: {
        version: '>=1.10.0',
      },
    },
    android: {
      gradle: {
        version: '>=7.0.0',
      },
      androidStudio: {
        version: '>=4.0.0',
      },
    },
  },

  // Configuration for different environments
  env: {
    development: {
      settings: {
        // Development-specific settings
        devMode: true,
        inlineRequires: true,
      },
    },
    production: {
      settings: {
        // Production-specific settings
        devMode: false,
        inlineRequires: false,
        minifyCode: true,
      },
    },
  },
};