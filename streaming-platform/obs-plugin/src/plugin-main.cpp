#include "plugin-main.h"
#include <QMessageBox>
#include <QMenuBar>
#include <QApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QTimer>
#include <iostream>

DnDStreamingPlugin *DnDStreamingPlugin::s_instance = nullptr;

DnDStreamingPlugin::DnDStreamingPlugin()
    : m_webSocket(nullptr)
    , m_reconnectTimer(new QTimer(this))
    , m_heartbeatTimer(new QTimer(this))
    , m_mainWindow(nullptr)
    , m_autoConnect(true)
    , m_reconnectInterval(5000)
    , m_connected(false)
    , m_streaming(false)
    , m_recording(false)
    , m_diceRollSource(nullptr)
    , m_characterDisplaySource(nullptr)
    , m_chatOverlaySource(nullptr)
    , m_donationAlertSource(nullptr)
{
    connect(m_reconnectTimer, &QTimer::timeout, this, [this]() {
        if (!m_connected) {
            connectToServer(m_serverUrl);
        }
    });

    connect(m_heartbeatTimer, &QTimer::timeout, this, [this]() {
        if (m_connected && m_webSocket) {
            QJsonObject heartbeat;
            heartbeat["type"] = "heartbeat";
            heartbeat["timestamp"] = QDateTime::currentMSecsSinceEpoch();
            m_webSocket->sendTextMessage(QJsonDocument(heartbeat).toJson());
        }
    });
}

DnDStreamingPlugin::~DnDStreamingPlugin()
{
    cleanup();
}

DnDStreamingPlugin &DnDStreamingPlugin::instance()
{
    if (!s_instance) {
        s_instance = new DnDStreamingPlugin();
    }
    return *s_instance;
}

bool DnDStreamingPlugin::initialize()
{
    blog(LOG_INFO, "[DnD Streaming Plugin] Initializing...");

    // Load settings
    loadSettings();

    // Find main OBS window
    QMainWindow *mainWindow = static_cast<QMainWindow*>(obs_frontend_get_main_window());
    if (mainWindow) {
        m_mainWindow = mainWindow;
        setupMenuActions();
    }

    // Register custom sources
    registerDnDSources();

    // Create D&D specific scenes
    createDnDScenes();

    // Create overlays
    createOverlays();

    // Connect to server if auto-connect is enabled
    if (m_autoConnect && !m_serverUrl.isEmpty()) {
        connectToServer(m_serverUrl);
    }

    blog(LOG_INFO, "[DnD Streaming Plugin] Initialized successfully");
    return true;
}

void DnDStreamingPlugin::cleanup()
{
    blog(LOG_INFO, "[DnD Streaming Plugin] Cleaning up...");

    disconnectFromServer();

    if (m_diceRollSource) {
        obs_source_release(m_diceRollSource);
        m_diceRollSource = nullptr;
    }
    if (m_characterDisplaySource) {
        obs_source_release(m_characterDisplaySource);
        m_characterDisplaySource = nullptr;
    }
    if (m_chatOverlaySource) {
        obs_source_release(m_chatOverlaySource);
        m_chatOverlaySource = nullptr;
    }
    if (m_donationAlertSource) {
        obs_source_release(m_donationAlertSource);
        m_donationAlertSource = nullptr;
    }
}

void DnDStreamingPlugin::connectToServer(const QString &url)
{
    if (m_webSocket) {
        m_webSocket->deleteLater();
    }

    m_webSocket = new QWebSocket();

    connect(m_webSocket, &QWebSocket::connected, this, [this]() {
        m_connected = true;
        m_reconnectTimer->stop();
        m_heartbeatTimer->start(30000); // Send heartbeat every 30 seconds

        blog(LOG_INFO, "[DnD Streaming Plugin] Connected to server");

        // Send initial connection message
        QJsonObject connectMsg;
        connectMsg["type"] = "obs-connect";
        connectMsg["version"] = "1.0.0";
        connectMsg["apiKey"] = m_apiKey;
        m_webSocket->sendTextMessage(QJsonDocument(connectMsg).toJson());
    });

    connect(m_webSocket, &QWebSocket::disconnected, this, [this]() {
        m_connected = false;
        m_heartbeatTimer->stop();
        m_reconnectTimer->start(m_reconnectInterval);

        blog(LOG_WARNING, "[DnD Streaming Plugin] Disconnected from server");
    });

    connect(m_webSocket, QOverload<QAbstractSocket::SocketError>::of(&QWebSocket::error),
        this, [this](QAbstractSocket::SocketError error) {
            blog(LOG_ERROR, "[DnD Streaming Plugin] WebSocket error: %s",
                 m_webSocket->errorString().toStdString().c_str());
        });

    connect(m_webSocket, &QWebSocket::textMessageReceived, this,
            [this](const QString &message) {
                setupWebSocketHandlers();
                QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
                if (doc.isObject()) {
                    handleServerMessage(doc.object());
                }
            });

    m_webSocket->open(url);
    m_serverUrl = url;
}

void DnDStreamingPlugin::disconnectFromServer()
{
    if (m_webSocket) {
        m_webSocket->close();
        m_webSocket->deleteLater();
        m_webSocket = nullptr;
    }
    m_connected = false;
    m_reconnectTimer->stop();
    m_heartbeatTimer->stop();
}

bool DnDStreamingPlugin::isConnected() const
{
    return m_connected;
}

void DnDStreamingPlugin::createDnDScenes()
{
    // Create D&D themed scenes
    obs_scene_t *scene;

    // Main Game Scene
    scene = obs_scene_create("D&D - Main Game");
    if (scene) {
        // Add default sources to main game scene
        obs_scene_release(scene);
    }

    // Combat Scene
    scene = obs_scene_create("D&D - Combat");
    if (scene) {
        // Add combat-specific sources
        obs_scene_release(scene);
    }

    // Character Sheets Scene
    scene = obs_scene_create("D&D - Character Sheets");
    if (scene) {
        // Add character display sources
        obs_scene_release(scene);
    }

    // Map Viewer Scene
    scene = obs_scene_create("D&D - Map Viewer");
    if (scene) {
        // Add map display sources
        obs_scene_release(scene);
    }

    // Starting Soon Scene
    scene = obs_scene_create("D&D - Starting Soon");
    if (scene) {
        // Add starting soon overlay
        obs_scene_release(scene);
    }

    // BRB Scene
    scene = obs_scene_create("D&D - Be Right Back");
    if (scene) {
        // Add BRB overlay
        obs_scene_release(scene);
    }

    blog(LOG_INFO, "[DnD Streaming Plugin] D&D scenes created");
}

void DnDStreamingPlugin::createOverlays()
{
    // Create dice roll source
    if (!m_diceRollSource) {
        obs_data_t *settings = obs_data_create();
        m_diceRollSource = createDiceRollSource(settings, nullptr);
        obs_data_release(settings);
    }

    // Create character display source
    if (!m_characterDisplaySource) {
        obs_data_t *settings = obs_data_create();
        m_characterDisplaySource = createCharacterDisplaySource(settings, nullptr);
        obs_data_release(settings);
    }

    // Create chat overlay source
    if (!m_chatOverlaySource) {
        obs_data_t *settings = obs_data_create();
        m_chatOverlaySource = createChatOverlaySource(settings, nullptr);
        obs_data_release(settings);
    }

    // Create donation alert source
    if (!m_donationAlertSource) {
        obs_data_t *settings = obs_data_create();
        m_donationAlertSource = createDonationAlertSource(settings, nullptr);
        obs_data_release(settings);
    }

    blog(LOG_INFO, "[DnD Streaming Plugin] D&D overlays created");
}

void DnDStreamingPlugin::setupMenuActions()
{
    if (!m_mainWindow) return;

    QMenu *pluginsMenu = m_mainWindow->findChild<QMenu*>("pluginsMenu");
    if (!pluginsMenu) {
        QMenuBar *menuBar = m_mainWindow->menuBar();
        pluginsMenu = menuBar->addMenu("Plugins");
    }

    if (pluginsMenu) {
        QAction *settingsAction = pluginsMenu->addAction("D&D Streaming Settings");
        connect(settingsAction, &QAction::triggered, this, &DnDStreamingPlugin::showSettingsDialog);

        QAction *connectAction = pluginsMenu->addAction("Connect to D&D Server");
        connect(connectAction, &QAction::triggered, this, [this]() {
            connectToServer(m_serverUrl);
        });

        QAction *disconnectAction = pluginsMenu->addAction("Disconnect from D&D Server");
        connect(disconnectAction, &QAction::triggered, this, &DnDStreamingPlugin::disconnectFromServer);
    }
}

void DnDStreamingPlugin::handleServerMessage(const QJsonObject &message)
{
    QString type = message["type"].toString();

    if (type == "switch-scene") {
        QString sceneName = message["scene"].toString();
        switchToScene(sceneName);
    } else if (type == "update-overlay") {
        QString overlayName = message["overlay"].toString();
        QJsonObject data = message["data"].toObject();
        updateOverlay(overlayName, data);
    } else if (type == "start-stream") {
        startStreaming();
    } else if (type == "stop-stream") {
        stopStreaming();
    } else if (type == "start-recording") {
        startRecording();
    } else if (type == "stop-recording") {
        stopRecording();
    } else if (type == "dice-roll") {
        // Handle dice roll animation
        updateOverlay("dice", message);
    } else if (type == "donation-alert") {
        // Handle donation alert
        updateOverlay("donation", message);
    }
}

void DnDStreamingPlugin::switchToScene(const QString &sceneName)
{
    obs_source_t *source = obs_get_source_by_name(sceneName.toUtf8().constData());
    if (source) {
        obs_frontend_set_current_scene(source);
        obs_source_release(source);
        blog(LOG_INFO, "[DnD Streaming Plugin] Switched to scene: %s",
             sceneName.toStdString().c_str());
    }
}

void DnDStreamingPlugin::updateOverlay(const QString &overlayName, const QJsonObject &data)
{
    // Update overlay based on type
    if (overlayName == "dice" && m_diceRollSource) {
        // Update dice roll animation
        obs_data_t *settings = obs_source_get_settings(m_diceRollSource);
        // Update settings with data
        obs_source_update(m_diceRollSource, settings);
        obs_data_release(settings);
    } else if (overlayName == "character" && m_characterDisplaySource) {
        // Update character display
        obs_data_t *settings = obs_source_get_settings(m_characterDisplaySource);
        // Update settings with data
        obs_source_update(m_characterDisplaySource, settings);
        obs_data_release(settings);
    } else if (overlayName == "chat" && m_chatOverlaySource) {
        // Update chat overlay
        obs_data_t *settings = obs_source_get_settings(m_chatOverlaySource);
        // Update settings with data
        obs_source_update(m_chatOverlaySource, settings);
        obs_data_release(settings);
    } else if (overlayName == "donation" && m_donationAlertSource) {
        // Update donation alert
        obs_data_t *settings = obs_source_get_settings(m_donationAlertSource);
        // Update settings with data
        obs_source_update(m_donationAlertSource, settings);
        obs_data_release(settings);
    }
}

void DnDStreamingPlugin::startStreaming()
{
    if (!obs_frontend_streaming_active()) {
        obs_frontend_start_streaming();
        m_streaming = true;
        blog(LOG_INFO, "[DnD Streaming Plugin] Stream started");
    }
}

void DnDStreamingPlugin::stopStreaming()
{
    if (obs_frontend_streaming_active()) {
        obs_frontend_stop_streaming();
        m_streaming = false;
        blog(LOG_INFO, "[DnD Streaming Plugin] Stream stopped");
    }
}

void DnDStreamingPlugin::startRecording()
{
    if (!obs_frontend_recording_active()) {
        obs_frontend_start_recording();
        m_recording = true;
        blog(LOG_INFO, "[DnD Streaming Plugin] Recording started");
    }
}

void DnDStreamingPlugin::stopRecording()
{
    if (obs_frontend_recording_active()) {
        obs_frontend_stop_recording();
        m_recording = false;
        blog(LOG_INFO, "[DnD Streaming Plugin] Recording stopped");
    }
}

void DnDStreamingPlugin::loadSettings()
{
    // Load settings from OBS config
    config_t *config = obs_frontend_get_global_config();
    if (config) {
        m_serverUrl = config_get_string(config, "DnDStreaming", "ServerUrl");
        m_apiKey = config_get_string(config, "DnDStreaming", "ApiKey");
        m_autoConnect = config_get_bool(config, "DnDStreaming", "AutoConnect");
        m_reconnectInterval = config_get_int(config, "DnDStreaming", "ReconnectInterval");
    }
}

void DnDStreamingPlugin::saveSettings()
{
    // Save settings to OBS config
    config_t *config = obs_frontend_get_global_config();
    if (config) {
        config_set_string(config, "DnDStreaming", "ServerUrl", m_serverUrl.toUtf8().constData());
        config_set_string(config, "DnDStreaming", "ApiKey", m_apiKey.toUtf8().constData());
        config_set_bool(config, "DnDStreaming", "AutoConnect", m_autoConnect);
        config_set_int(config, "DnDStreaming", "ReconnectInterval", m_reconnectInterval);
        config_save(config);
    }
}

void DnDStreamingPlugin::showSettingsDialog()
{
    // Show settings dialog (implementation in settings-dialog.cpp)
    // This is a placeholder - actual implementation would create a Qt dialog
    QMessageBox::information(nullptr, "D&D Streaming Settings",
                           "Settings dialog implementation needed");
}

// OBS module entry points
extern "C" void obs_module_load()
{
    blog(LOG_INFO, "[DnD Streaming Plugin] Loading plugin...");
    DnDStreamingPlugin::instance().initialize();
}

extern "C" void obs_module_unload()
{
    blog(LOG_INFO, "[DnD Streaming Plugin] Unloading plugin...");
    DnDStreamingPlugin::instance().cleanup();
}

extern "C" const char *obs_module_name()
{
    return "D&D Streaming Plugin";
}

extern "C" const char *obs_module_description()
{
    return "Professional streaming integration for D&D sessions with scene management, overlays, and real-time updates";
}

extern "C" const char *obs_module_author()
{
    return "DMlogn8n Streaming Platform";
}

extern "C" const char *obs_module_version()
{
    return "1.0.0";
}