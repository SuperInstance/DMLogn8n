using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using SimpleJSON;
using WebSocketSharp;

namespace DMLogn8n.FeatureFlags
{
    /// <summary>
    /// Represents a feature flag value with metadata
    /// </summary>
    [Serializable]
    public class FeatureFlagValue
    {
        public string flagId;
        public object value;
        public string variant;
        public string experimentId;
        public DateTime timestamp;

        public FeatureFlagValue()
        {
            timestamp = DateTime.UtcNow;
        }

        public FeatureFlagValue(string flagId, object value, string variant = null, string experimentId = null, DateTime? timestamp = null)
        {
            this.flagId = flagId;
            this.value = value;
            this.variant = variant;
            this.experimentId = experimentId;
            this.timestamp = timestamp ?? DateTime.UtcNow;
        }
    }

    /// <summary>
    /// Represents an experiment variant assignment
    /// </summary>
    [Serializable]
    public class ExperimentVariant
    {
        public string variantId;
        public string variantName;
        public string configJson;
        public bool isControl;

        public Dictionary<string, object> GetConfig()
        {
            if (string.IsNullOrEmpty(configJson))
                return new Dictionary<string, object>();

            try
            {
                return JsonConvert.DeserializeObject<Dictionary<string, object>>(configJson);
            }
            catch
            {
                return new Dictionary<string, object>();
            }
        }
    }

    /// <summary>
    /// Represents an experiment assignment
    /// </summary>
    [Serializable]
    public class ExperimentAssignment
    {
        public string experimentId;
        public ExperimentVariant variant;
        public DateTime timestamp;

        public ExperimentAssignment()
        {
            timestamp = DateTime.UtcNow;
        }

        public ExperimentAssignment(string experimentId, ExperimentVariant variant, DateTime? timestamp = null)
        {
            this.experimentId = experimentId;
            this.variant = variant;
            this.timestamp = timestamp ?? DateTime.UtcNow;
        }
    }

    /// <summary>
    /// Delegate for flag change events
    /// </summary>
    /// <param name="flagValue">The new flag value</param>
    public delegate void FlagChangeHandler(FeatureFlagValue flagValue);

    /// <summary>
    /// Delegate for experiment assignment events
    /// </summary>
    /// <param name="assignment">The experiment assignment</param>
    public delegate void ExperimentHandler(ExperimentAssignment assignment);

    /// <summary>
    /// DMLogn8n Feature Flag SDK for Unity
    /// </summary>
    public class DMLogn8nSDK : MonoBehaviour
    {
        [Header("Configuration")]
        [SerializeField] private string apiBaseUrl = "http://localhost:8001";
        [SerializeField] private string sdkKey = "";
        [SerializeField] private string userId = "";
        [SerializeField] private bool enableStreaming = false;
        [SerializeField] private bool debugLogging = false;
        [SerializeField] private int cacheTtlSeconds = 300; // 5 minutes

        [Header("Runtime")]
        [SerializeField] private bool isInitialized = false;

        // Private fields
        private Dictionary<string, object> context = new Dictionary<string, object>();
        private Dictionary<string, FeatureFlagValue> flagCache = new Dictionary<string, FeatureFlagValue>();
        private Dictionary<string, ExperimentAssignment> experimentCache = new Dictionary<string, ExperimentAssignment>();
        private Dictionary<string, float> cacheTimestamps = new Dictionary<string, float>();
        private Dictionary<string, List<FlagChangeHandler>> flagChangeHandlers = new Dictionary<string, List<FlagChangeHandler>>();
        private List<ExperimentHandler> experimentHandlers = new List<ExperimentHandler>();

        private WebSocket websocket;
        private CancellationTokenSource cancellationTokenSource;
        private readonly object lockObject = new object();

        // Events
        public event Action OnInitialized;
        public event Action<string> OnError;

        #region Properties

        /// <summary>
        /// Gets whether the SDK is initialized
        /// </summary>
        public bool IsInitialized => isInitialized;

        /// <summary>
        /// Gets or sets the current user ID
        /// </summary>
        public string UserId
        {
            get => userId;
            set
            {
                if (userId != value)
                {
                    userId = value;
                    ClearUserCache();
                    Log($"User ID set to: {userId}");
                }
            }
        }

        #endregion

        #region Unity Lifecycle

        private void Awake()
        {
            // Make this object persistent across scenes
            if (FindObjectsOfType<DMLogn8nSDK>().Length > 1)
            {
                Destroy(gameObject);
                return;
            }

            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            InitializeAsync();
        }

        private void OnDestroy()
        {
            Destroy();
        }

        private void OnApplicationQuit()
        {
            Destroy();
        }

        #endregion

        #region Initialization

        /// <summary>
        /// Initialize the SDK
        /// </summary>
        public async void InitializeAsync()
        {
            if (isInitialized)
            {
                Log("SDK already initialized");
                return;
            }

            try
            {
                cancellationTokenSource = new CancellationTokenSource();

                // Set up streaming if enabled
                if (enableStreaming)
                {
                    SetupStreaming();
                }

                isInitialized = true;
                OnInitialized?.Invoke();
                Log("SDK initialized successfully");
            }
            catch (Exception ex)
            {
                LogError($"Failed to initialize SDK: {ex.Message}");
                OnError?.Invoke(ex.Message);
            }
        }

        /// <summary>
        /// Destroy the SDK and clean up resources
        /// </summary>
        public void Destroy()
        {
            if (websocket != null)
            {
                websocket.Close();
                websocket = null;
            }

            cancellationTokenSource?.Cancel();
            cancellationTokenSource?.Dispose();

            flagCache.Clear();
            experimentCache.Clear();
            cacheTimestamps.Clear();
            flagChangeHandlers.Clear();
            experimentHandlers.Clear();

            isInitialized = false;
            Log("SDK destroyed");
        }

        #endregion

        #region User Management

        /// <summary>
        /// Set the current user and context
        /// </summary>
        /// <param name="userId">User ID</param>
        /// <param name="context">Additional context</param>
        public void SetUser(string userId, Dictionary<string, object> context = null)
        {
            UserId = userId;

            if (context != null)
            {
                foreach (var kvp in context)
                {
                    this.context[kvp.Key] = kvp.Value;
                }
            }

            ClearUserCache();
            Log($"User set: {userId}");
        }

        /// <summary>
        /// Update user context
        /// </summary>
        /// <param name="context">Context updates</param>
        public void UpdateContext(Dictionary<string, object> context)
        {
            if (context != null)
            {
                foreach (var kvp in context)
                {
                    this.context[kvp.Key] = kvp.Value;
                }
            }

            ClearUserCache();
            Log("Context updated");
        }

        /// <summary>
        /// Add context value
        /// </summary>
        /// <param name="key">Context key</param>
        /// <param name="value">Context value</param>
        public void AddContext(string key, object value)
        {
            context[key] = value;
            ClearUserCache();
            Log($"Context added: {key} = {value}");
        }

        #endregion

        #region Feature Flags

        /// <summary>
        /// Get a feature flag value
        /// </summary>
        /// <param name="flagName">Name of the flag</param>
        /// <param name="defaultValue">Default value if flag is not found</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>Feature flag value</returns>
        public async Task<FeatureFlagValue> GetFlagAsync(string flagName, object defaultValue = null, string userId = null, Dictionary<string, object> context = null)
        {
            if (!isInitialized)
            {
                LogError("SDK not initialized");
                return new FeatureFlagValue("error", defaultValue);
            }

            string effectiveUserId = userId ?? UserId;
            if (string.IsNullOrEmpty(effectiveUserId))
            {
                LogWarning("No user_id provided for flag evaluation");
                return new FeatureFlagValue("error", defaultValue);
            }

            Dictionary<string, object> effectiveContext = new Dictionary<string, object>(this.context);
            if (context != null)
            {
                foreach (var kvp in context)
                {
                    effectiveContext[kvp.Key] = kvp.Value;
                }
            }

            // Check cache first
            string cacheKey = $"flag:{effectiveUserId}:{flagName}";
            if (TryGetFromCache(cacheKey, out FeatureFlagValue cachedValue) && !IsCacheExpired(cacheKey))
            {
                Log($"Cache hit for flag: {flagName}");
                return cachedValue;
            }

            try
            {
                string url = $"{apiBaseUrl}/evaluate";
                var requestBody = new
                {
                    user_id = effectiveUserId,
                    flag_name = flagName,
                    context = effectiveContext
                };

                string jsonBody = JsonConvert.SerializeObject(requestBody);
                using var webRequest = UnityWebRequest.Put(url, jsonBody);
                webRequest.method = "POST";
                webRequest.SetRequestHeader("Content-Type", "application/json");

                if (!string.IsNullOrEmpty(sdkKey))
                {
                    webRequest.SetRequestHeader("Authorization", $"Bearer {sdkKey}");
                }

                var operation = webRequest.SendWebRequest();
                while (!operation.isDone)
                {
                    await Task.Yield();
                }

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    string responseJson = webRequest.downloadHandler.text;
                    var responseData = JsonConvert.DeserializeObject<Dictionary<string, object>>(responseJson);

                    var flagValue = new FeatureFlagValue(
                        responseData["flag_id"].ToString(),
                        responseData["value"],
                        responseData.Contains("variant") ? responseData["variant"].ToString() : null,
                        responseData.Contains("experiment_id") ? responseData["experiment_id"].ToString() : null,
                        DateTime.Parse(responseData["timestamp"].ToString())
                    );

                    // Cache the result
                    SetCache(cacheKey, flagValue);
                    Log($"Retrieved flag: {flagName} = {flagValue.value}");
                    return flagValue;
                }
                else
                {
                    LogError($"Failed to get flag {flagName}: {webRequest.error}");
                    return new FeatureFlagValue("error", defaultValue);
                }
            }
            catch (Exception ex)
            {
                LogError($"Error getting flag {flagName}: {ex.Message}");
                return new FeatureFlagValue("error", defaultValue);
            }
        }

        /// <summary>
        /// Check if a boolean flag is enabled
        /// </summary>
        /// <param name="flagName">Name of the flag</param>
        /// <param name="defaultValue">Default value</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>True if flag is enabled</returns>
        public async Task<bool> IsEnabledAsync(string flagName, bool defaultValue = false, string userId = null, Dictionary<string, object> context = null)
        {
            var flagValue = await GetFlagAsync(flagName, defaultValue, userId, context);
            return Convert.ToBoolean(flagValue.value);
        }

        /// <summary>
        /// Get string flag value
        /// </summary>
        /// <param name="flagName">Name of the flag</param>
        /// <param name="defaultValue">Default value</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>String value</returns>
        public async Task<string> GetStringValueAsync(string flagName, string defaultValue = "", string userId = null, Dictionary<string, object> context = null)
        {
            var flagValue = await GetFlagAsync(flagName, defaultValue, userId, context);
            return flagValue.value?.ToString() ?? defaultValue;
        }

        /// <summary>
        /// Get number flag value
        /// </summary>
        /// <param name="flagName">Name of the flag</param>
        /// <param name="defaultValue">Default value</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>Number value</returns>
        public async Task<float> GetNumberValueAsync(string flagName, float defaultValue = 0f, string userId = null, Dictionary<string, object> context = null)
        {
            var flagValue = await GetFlagAsync(flagName, defaultValue, userId, context);
            if (float.TryParse(flagValue.value?.ToString(), out float result))
            {
                return result;
            }
            return defaultValue;
        }

        /// <summary>
        /// Get JSON flag value
        /// </summary>
        /// <param name="flagName">Name of the flag</param>
        /// <param name="defaultValue">Default value</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>Dictionary value</returns>
        public async Task<Dictionary<string, object>> GetJsonValueAsync(string flagName, Dictionary<string, object> defaultValue = null, string userId = null, Dictionary<string, object> context = null)
        {
            if (defaultValue == null)
                defaultValue = new Dictionary<string, object>();

            var flagValue = await GetFlagAsync(flagName, defaultValue, userId, context);

            if (flagValue.value is Dictionary<string, object> dict)
            {
                return dict;
            }

            if (flagValue.value is string jsonString)
            {
                try
                {
                    return JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonString);
                }
                catch
                {
                    return defaultValue;
                }
            }

            return defaultValue;
        }

        #endregion

        #region Experiments

        /// <summary>
        /// Get experiment assignment for a user
        /// </summary>
        /// <param name="experimentId">Experiment ID</param>
        /// <param name="userId">Optional user ID override</param>
        /// <param name="context">Additional context</param>
        /// <returns>Experiment assignment or null</returns>
        public async Task<ExperimentAssignment> GetExperimentAssignmentAsync(string experimentId, string userId = null, Dictionary<string, object> context = null)
        {
            if (!isInitialized)
            {
                LogError("SDK not initialized");
                return null;
            }

            string effectiveUserId = userId ?? UserId;
            if (string.IsNullOrEmpty(effectiveUserId))
            {
                LogWarning("No user_id provided for experiment assignment");
                return null;
            }

            Dictionary<string, object> effectiveContext = new Dictionary<string, object>(this.context);
            if (context != null)
            {
                foreach (var kvp in context)
                {
                    effectiveContext[kvp.Key] = kvp.Value;
                }
            }

            // Check cache first
            string cacheKey = $"experiment:{effectiveUserId}:{experimentId}";
            if (TryGetFromCache(cacheKey, out ExperimentAssignment cachedAssignment) && !IsCacheExpired(cacheKey))
            {
                Log($"Cache hit for experiment: {experimentId}");
                return cachedAssignment;
            }

            try
            {
                // This would integrate with the experiment manager
                // For now, return a placeholder
                var assignment = new ExperimentAssignment(
                    experimentId,
                    new ExperimentVariant
                    {
                        variantId = "control",
                        variantName = "Control",
                        configJson = "{}",
                        isControl = true
                    }
                );

                // Cache the assignment
                SetCache(cacheKey, assignment);
                Log($"Retrieved experiment assignment: {experimentId}");
                return assignment;
            }
            catch (Exception ex)
            {
                LogError($"Error getting experiment assignment: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Track a metric for an experiment
        /// </summary>
        /// <param name="experimentId">Experiment ID</param>
        /// <param name="metricName">Metric name</param>
        /// <param name="value">Metric value</param>
        /// <param name="userId">Optional user ID override</param>
        public async Task TrackMetricAsync(string experimentId, string metricName, float value, string userId = null)
        {
            if (!isInitialized)
            {
                LogError("SDK not initialized");
                return;
            }

            string effectiveUserId = userId ?? UserId;
            if (string.IsNullOrEmpty(effectiveUserId))
            {
                LogWarning("No user_id provided for metric tracking");
                return;
            }

            try
            {
                string url = $"{apiBaseUrl}/metrics";
                var requestBody = new
                {
                    experiment_id = experimentId,
                    metric_name = metricName,
                    value = value,
                    user_id = effectiveUserId,
                    timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
                };

                string jsonBody = JsonConvert.SerializeObject(requestBody);
                using var webRequest = UnityWebRequest.Put(url, jsonBody);
                webRequest.method = "POST";
                webRequest.SetRequestHeader("Content-Type", "application/json");

                if (!string.IsNullOrEmpty(sdkKey))
                {
                    webRequest.SetRequestHeader("Authorization", $"Bearer {sdkKey}");
                }

                var operation = webRequest.SendWebRequest();
                while (!operation.isDone)
                {
                    await Task.Yield();
                }

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    Log($"Tracked metric: {metricName} = {value}");
                }
                else
                {
                    LogError($"Failed to track metric: {webRequest.error}");
                }
            }
            catch (Exception ex)
            {
                LogError($"Error tracking metric: {ex.Message}");
            }
        }

        #endregion

        #region Event Handlers

        /// <summary>
        /// Add a handler for flag changes
        /// </summary>
        /// <param name="flagName">Flag name</param>
        /// <param name="handler">Handler function</param>
        public void AddFlagChangeHandler(string flagName, FlagChangeHandler handler)
        {
            lock (lockObject)
            {
                if (!flagChangeHandlers.ContainsKey(flagName))
                {
                    flagChangeHandlers[flagName] = new List<FlagChangeHandler>();
                }
                flagChangeHandlers[flagName].Add(handler);
            }
            Log($"Added handler for flag: {flagName}");
        }

        /// <summary>
        /// Add a handler for experiment assignments
        /// </summary>
        /// <param name="handler">Handler function</param>
        public void AddExperimentHandler(ExperimentHandler handler)
        {
            lock (lockObject)
            {
                experimentHandlers.Add(handler);
            }
            Log("Added experiment handler");
        }

        #endregion

        #region Cache Management

        /// <summary>
        /// Get value from cache
        /// </summary>
        /// <param name="key">Cache key</param>
        /// <param name="value">Output value</param>
        /// <returns>True if value was found and not expired</returns>
        private bool TryGetFromCache(string key, out FeatureFlagValue value)
        {
            lock (lockObject)
            {
                if (flagCache.TryGetValue(key, out value))
                {
                    return !IsCacheExpired(key);
                }
            }
            value = null;
            return false;
        }

        /// <summary>
        /// Get value from cache
        /// </summary>
        /// <param name="key">Cache key</param>
        /// <param name="value">Output value</param>
        /// <returns>True if value was found and not expired</returns>
        private bool TryGetFromCache(string key, out ExperimentAssignment value)
        {
            lock (lockObject)
            {
                if (experimentCache.TryGetValue(key, out value))
                {
                    return !IsCacheExpired(key);
                }
            }
            value = null;
            return false;
        }

        /// <summary>
        /// Set value in cache
        /// </summary>
        /// <param name="key">Cache key</param>
        /// <param name="value">Value to cache</param>
        private void SetCache(string key, FeatureFlagValue value)
        {
            lock (lockObject)
            {
                flagCache[key] = value;
                cacheTimestamps[key] = Time.time;
            }
        }

        /// <summary>
        /// Set value in cache
        /// </summary>
        /// <param name="key">Cache key</param>
        /// <param name="value">Value to cache</param>
        private void SetCache(string key, ExperimentAssignment value)
        {
            lock (lockObject)
            {
                experimentCache[key] = value;
                cacheTimestamps[key] = Time.time;
            }
        }

        /// <summary>
        /// Check if cache entry is expired
        /// </summary>
        /// <param name="key">Cache key</param>
        /// <returns>True if expired</returns>
        private bool IsCacheExpired(string key)
        {
            lock (lockObject)
            {
                if (!cacheTimestamps.ContainsKey(key))
                    return true;

                return Time.time - cacheTimestamps[key] > cacheTtlSeconds;
            }
        }

        /// <summary>
        /// Clear user-specific cache entries
        /// </summary>
        private void ClearUserCache()
        {
            if (string.IsNullOrEmpty(userId))
                return;

            lock (lockObject)
            {
                // Clear flag cache for this user
                var flagKeysToRemove = new List<string>();
                foreach (var key in flagCache.Keys)
                {
                    if (key.StartsWith($"flag:{userId}:"))
                    {
                        flagKeysToRemove.Add(key);
                    }
                }

                foreach (var key in flagKeysToRemove)
                {
                    flagCache.Remove(key);
                    cacheTimestamps.Remove(key);
                }

                // Clear experiment cache for this user
                var experimentKeysToRemove = new List<string>();
                foreach (var key in experimentCache.Keys)
                {
                    if (key.StartsWith($"experiment:{userId}:"))
                    {
                        experimentKeysToRemove.Add(key);
                    }
                }

                foreach (var key in experimentKeysToRemove)
                {
                    experimentCache.Remove(key);
                    cacheTimestamps.Remove(key);
                }
            }
        }

        /// <summary>
        /// Flush all cache entries
        /// </summary>
        public void FlushCache()
        {
            lock (lockObject)
            {
                flagCache.Clear();
                experimentCache.Clear();
                cacheTimestamps.Clear();
            }
            Log("Cache flushed");
        }

        #endregion

        #region Streaming

        /// <summary>
        /// Set up WebSocket streaming for real-time updates
        /// </summary>
        private void SetupStreaming()
        {
            try
            {
                string wsUrl = apiBaseUrl.Replace("http://", "ws://").Replace("https://", "wss://") + "/ws";
                websocket = new WebSocket(wsUrl);

                websocket.OnOpen += (sender, e) =>
                {
                    Log("WebSocket connection established");
                };

                websocket.OnMessage += (sender, e) =>
                {
                    HandleWebSocketMessage(e.Data);
                };

                websocket.OnError += (sender, e) =>
                {
                    Log($"WebSocket error: {e.Message}");
                };

                websocket.OnClose += (sender, e) =>
                {
                    Log("WebSocket connection closed");
                    // Attempt to reconnect after 5 seconds
                    StartCoroutine(ReconnectWebSocket());
                };

                websocket.ConnectAsync();
            }
            catch (Exception ex)
            {
                LogError($"Failed to setup streaming: {ex.Message}");
            }
        }

        /// <summary>
        /// Reconnect WebSocket
        /// </summary>
        /// <returns></returns>
        private IEnumerator ReconnectWebSocket()
        {
            yield return new WaitForSeconds(5f);
            if (enableStreaming && websocket == null)
            {
                SetupStreaming();
            }
        }

        /// <summary>
        /// Handle WebSocket messages
        /// </summary>
        /// <param name="message">Message data</param>
        private void HandleWebSocketMessage(string message)
        {
            try
            {
                var data = JsonConvert.DeserializeObject<Dictionary<string, object>>(message);

                if (data.ContainsKey("type"))
                {
                    string type = data["type"].ToString();

                    if (type == "flag_change")
                    {
                        HandleFlagChange(data);
                    }
                    else if (type == "experiment_update")
                    {
                        HandleExperimentUpdate(data);
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error handling WebSocket message: {ex.Message}");
            }
        }

        /// <summary>
        /// Handle flag change notifications
        /// </summary>
        /// <param name="data">Flag change data</param>
        private void HandleFlagChange(Dictionary<string, object> data)
        {
            try
            {
                if (data.ContainsKey("flag"))
                {
                    var flagData = JsonConvert.DeserializeObject<Dictionary<string, object>>(data["flag"].ToString());
                    string flagName = flagData["name"].ToString();

                    lock (lockObject)
                    {
                        if (flagChangeHandlers.ContainsKey(flagName))
                        {
                            // Invalidate cache for this flag
                            var keysToRemove = new List<string>();
                            foreach (var key in flagCache.Keys)
                            {
                                if (key.EndsWith($":{flagName}"))
                                {
                                    keysToRemove.Add(key);
                                }
                            }

                            foreach (var key in keysToRemove)
                            {
                                flagCache.Remove(key);
                                cacheTimestamps.Remove(key);
                            }

                            // Call handlers
                            var flagValue = new FeatureFlagValue(
                                flagData["id"].ToString(),
                                flagData["current_value"],
                                flagData.Contains("variant") ? flagData["variant"].ToString() : null,
                                flagData.Contains("experiment_id") ? flagData["experiment_id"].ToString() : null,
                                DateTime.Parse(data["timestamp"].ToString())
                            );

                            foreach (var handler in flagChangeHandlers[flagName])
                            {
                                try
                                {
                                    handler(flagValue);
                                }
                                catch (Exception ex)
                                {
                                    LogError($"Error in flag change handler: {ex.Message}");
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error handling flag change: {ex.Message}");
            }
        }

        /// <summary>
        /// Handle experiment update notifications
        /// </summary>
        /// <param name="data">Experiment update data</param>
        private void HandleExperimentUpdate(Dictionary<string, object> data)
        {
            try
            {
                lock (lockObject)
                {
                    // Clear experiment cache
                    var keysToRemove = new List<string>();
                    foreach (var key in experimentCache.Keys)
                    {
                        if (key.StartsWith("experiment:"))
                        {
                            keysToRemove.Add(key);
                        }
                    }

                    foreach (var key in keysToRemove)
                    {
                        experimentCache.Remove(key);
                        cacheTimestamps.Remove(key);
                    }

                    // Call experiment handlers
                    foreach (var handler in experimentHandlers)
                    {
                        try
                        {
                            handler(null); // Could pass actual data if needed
                        }
                        catch (Exception ex)
                        {
                            LogError($"Error in experiment handler: {ex.Message}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError($"Error handling experiment update: {ex.Message}");
            }
        }

        #endregion

        #region Logging

        /// <summary>
        /// Log message if debug is enabled
        /// </summary>
        /// <param name="message">Log message</param>
        private void Log(string message)
        {
            if (debugLogging)
            {
                Debug.Log($"[DMLogn8n SDK] {message}");
            }
        }

        /// <summary>
        /// Log warning message
        /// </summary>
        /// <param name="message">Warning message</param>
        private void LogWarning(string message)
        {
            if (debugLogging)
            {
                Debug.LogWarning($"[DMLogn8n SDK] {message}");
            }
        }

        /// <summary>
        /// Log error message
        /// </summary>
        /// <param name="message">Error message</param>
        private void LogError(string message)
        {
            Debug.LogError($"[DMLogn8n SDK] {message}");
        }

        #endregion
    }

    /// <summary>
    /// Convenience wrapper for common feature flag operations
    /// </summary>
    public class FeatureFlags
    {
        private DMLogn8nSDK sdk;

        public FeatureFlags(DMLogn8nSDK sdk)
        {
            this.sdk = sdk;
        }

        /// <summary>
        /// Check if enhanced AI model is enabled for user
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>True if enhanced AI model is enabled</returns>
        public async Task<bool> IsAIModelEnhanced(string userId = null)
        {
            return await sdk.IsEnabledAsync("ai_model_enhanced", false, userId);
        }

        /// <summary>
        /// Get AI model to use for user
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>AI model name</returns>
        public async Task<string> GetAIModel(string userId = null)
        {
            return await sdk.GetStringValueAsync("ai_model_selection", "gpt-4", userId);
        }

        /// <summary>
        /// Check if voice chat is enabled for user
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>True if voice chat is enabled</returns>
        public async Task<bool> IsVoiceChatEnabled(string userId = null)
        {
            return await sdk.IsEnabledAsync("voice_chat_enabled", false, userId);
        }

        /// <summary>
        /// Get combat damage calculation method
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>Damage calculation method</returns>
        public async Task<string> GetCombatDamageMethod(string userId = null)
        {
            return await sdk.GetStringValueAsync("combat_damage_calculation", "standard", userId);
        }

        /// <summary>
        /// Check if enhanced UI is enabled for user
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>True if enhanced UI is enabled</returns>
        public async Task<bool> IsEnhancedUIEnabled(string userId = null)
        {
            return await sdk.IsEnabledAsync("enhanced_ui_animations", false, userId);
        }

        /// <summary>
        /// Get AI creativity level for user
        /// </summary>
        /// <param name="userId">Optional user ID</param>
        /// <returns>AI creativity level</returns>
        public async Task<float> GetAICreativityLevel(string userId = null)
        {
            return await sdk.GetNumberValueAsync("ai_response_creativity", 0.7f, userId);
        }
    }
}