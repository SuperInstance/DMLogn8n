#pragma once

#include <obs-module.h>
#include <obs-frontend-api.h>
#include <util/dstr.h>
#include <util/platform.h>
#include <QAction>
#include <QMainWindow>
#include <QTimer>
#include <QWebSocket>
#include <QJsonObject>
#include <QJsonDocument>

extern "C" {
    extern void obs_module_load();
    extern void obs_module_unload();
    extern const char *obs_module_name();
    extern const char *obs_module_description();
    extern const char *obs_module_author();
    extern const char *obs_module_version();
}

class DnDStreamingPlugin {
public:
    static DnDStreamingPlugin &instance();

    bool initialize();
    void cleanup();

    // WebSocket connection to main server
    void connectToServer(const QString &url);
    void disconnectFromServer();
    bool isConnected() const;

    // Scene management
    void createDnDScenes();
    void switchToScene(const QString &sceneName);

    // Overlay management
    void createOverlays();
    void updateOverlay(const QString &overlayName, const QJsonObject &data);

    // Stream control
    void startStreaming();
    void stopStreaming();
    void startRecording();
    void stopRecording();

    // Settings
    void loadSettings();
    void saveSettings();
    void showSettingsDialog();

private:
    DnDStreamingPlugin();
    ~DnDStreamingPlugin();

    void setupMenuActions();
    void setupWebSocketHandlers();

    QWebSocket *m_webSocket;
    QTimer *m_reconnectTimer;
    QTimer *m_heartbeatTimer;
    QMainWindow *m_mainWindow;

    // Settings
    QString m_serverUrl;
    QString m_apiKey;
    bool m_autoConnect;
    int m_reconnectInterval;

    // State
    bool m_connected;
    bool m_streaming;
    bool m_recording;

    // OBS references
    obs_source_t *m_diceRollSource;
    obs_source_t *m_characterDisplaySource;
    obs_source_t *m_chatOverlaySource;
    obs_source_t *m_donationAlertSource;

    static DnDStreamingPlugin *s_instance;
};

// Global functions
obs_source_t *createDiceRollSource(obs_data_t *settings, obs_source_t *source);
obs_source_t *createCharacterDisplaySource(obs_data_t *settings, obs_source_t *source);
obs_source_t *createChatOverlaySource(obs_data_t *settings, obs_source_t *source);
obs_source_t *createDonationAlertSource(obs_data_t *settings, obs_source_t *source);

void registerDnDSources();