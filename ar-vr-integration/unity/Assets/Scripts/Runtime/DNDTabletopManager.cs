using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Management;
using System.Collections.Generic;
using System.Collections;

namespace DND.ARVR
{
    /// <summary>
    /// Main manager for D&D VR Tabletop experience in Unity
    /// Handles VR/AR initialization, tabletop setup, and game state management
    /// </summary>
    public class DNDTabletopManager : MonoBehaviour
    {
        [Header("VR/AR Settings")]
        [SerializeField] private bool enableVR = true;
        [SerializeField] private bool enableAR = false;
        [SerializeField] private XRRig xrRig;
        [SerializeField] private XRInteractionManager interactionManager;

        [Header("Tabletop Settings")]
        [SerializeField] private GameObject tabletopPrefab;
        [SerializeField] private Vector3 tabletopScale = new Vector3(8f, 1f, 8f);
        [SerializeField] private Material tabletopMaterial;

        [Header("Player Settings")]
        [SerializeField] private GameObject playerPrefab;
        [SerializeField] private int maxPlayers = 6;
        [SerializeField] private float spawnRadius = 2f;

        [Header("Miniature Settings")]
        [SerializeField] private GameObject[] miniaturePrefabs;
        [SerializeField] private LayerMask miniatureLayer;
        [SerializeField] private float miniatureScale = 0.1f;

        [Header("Dice Settings")]
        [SerializeField] private GameObject[] dicePrefabs;
        [SerializeField] private Transform diceSpawnPoint;
        [SerializeField] private float diceThrowForce = 5f;

        [Header("Lighting Settings")]
        [SerializeField] private Light mainLight;
        [SerializeField] private Light[] ambientLights;
        [SerializeField] private Color dayLightColor = Color.white;
        [SerializeField] private Color dungeonLightColor = new Color(0.8f, 0.6f, 0.4f);

        [Header("Performance Settings")]
        [SerializeField] private int targetFrameRate = 90;
        [SerializeField] private bool enableAdaptiveQuality = true;
        [SerializeField] private bool enableOcclusion = true;

        // Runtime state
        private GameObject tabletopInstance;
        private List<GameObject> players = new List<GameObject>();
        private List<GameObject> miniatures = new List<GameObject>();
        private List<GameObject> dice = new List<GameObject>();
        private bool isInitialized = false;
        private bool isVRActive = false;
        private bool isARActive = false;

        // Performance monitoring
        private float currentFPS;
        private int frameCount;
        private float lastFPSTime;

        // Events
        public System.Action OnVRInitialized;
        public System.Action OnARInitialized;
        public System.Action OnTabletopCreated;
        public System.Action OnPlayerJoined;
        public System.Action OnPerformanceLevelChanged;

        private void Awake()
        {
            InitializeQualitySettings();
            Application.targetFrameRate = targetFrameRate;
        }

        private void Start()
        {
            StartCoroutine(InitializeXR());
        }

        private void Update()
        {
            UpdatePerformanceMetrics();

            if (enableAdaptiveQuality)
            {
                AdjustQualityBasedOnPerformance();
            }

            HandleInput();
        }

        private IEnumerator InitializeXR()
        {
            Debug.Log("Initializing XR...");

            // Initialize XR General Settings
            var xrManagerSettings = XRGeneralSettings.Instance;
            if (xrManagerSettings == null)
            {
                Debug.LogError("XR General Settings not found!");
                yield break;
            }

            var xrLoader = xrManagerSettings.Manager.loader;
            if (xrLoader == null)
            {
                Debug.LogError("XR Loader not found!");
                yield break;
            }

            // Initialize XR subsystems
            yield return xrLoader.Initialize();

            if (enableVR)
            {
                yield return StartCoroutine(InitializeVR());
            }

            if (enableAR)
            {
                yield return StartCoroutine(InitializeAR());
            }

            // Create tabletop after XR is ready
            CreateTabletop();

            isInitialized = true;
            Debug.Log("D&D Tabletop initialized successfully!");
        }

        private IEnumerator InitializeVR()
        {
            Debug.Log("Initializing VR...");

            // Start VR session
            var xrManager = XRGeneralSettings.Instance.Manager;
            yield return xrManager.StartSubsystems();

            // Setup VR-specific settings
            if (xrRig != null)
            {
                xrRig.gameObject.SetActive(true);
                SetupVRControllers();
            }

            // Configure VR camera
            ConfigureVRCamera();

            isVRActive = true;
            OnVRInitialized?.Invoke();

            Debug.Log("VR initialized successfully!");
        }

        private IEnumerator InitializeAR()
        {
            Debug.Log("Initializing AR...");

            // Start AR session
            var xrManager = XRGeneralSettings.Instance.Manager;
            yield return xrManager.StartSubsystems();

            // Setup AR-specific settings
            SetupARSession();
            ConfigureARCamera();

            isARActive = true;
            OnARInitialized?.Invoke();

            Debug.Log("AR initialized successfully!");
        }

        private void CreateTabletop()
        {
            if (tabletopPrefab == null)
            {
                Debug.LogError("Tabletop prefab not assigned!");
                return;
            }

            // Instantiate tabletop
            tabletopInstance = Instantiate(tabletopPrefab, Vector3.zero, Quaternion.identity);
            tabletopInstance.transform.localScale = tabletopScale;

            // Apply custom material if assigned
            if (tabletopMaterial != null)
            {
                var renderer = tabletopInstance.GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material = tabletopMaterial;
                }
            }

            // Add physics to tabletop
            var rigidbody = tabletopInstance.AddComponent<Rigidbody>();
            rigidbody.isKinematic = true;

            // Add colliders for interaction
            var colliders = tabletopInstance.GetComponentsInChildren<Collider>();
            foreach (var collider in colliders)
            {
                collider.gameObject.layer = LayerMask.NameToLayer("Tabletop");
            }

            // Spawn initial miniatures
            SpawnInitialMiniatures();

            OnTabletopCreated?.Invoke();

            Debug.Log("Tabletop created successfully!");
        }

        private void SpawnInitialMiniatures()
        {
            // Spawn player miniatures
            for (int i = 0; i < maxPlayers; i++)
            {
                var position = GetSpawnPosition(i);
                SpawnMiniature(0, position); // Use first prefab as player
            }

            // Spawn some monster miniatures
            for (int i = 0; i < 3; i++)
            {
                var position = GetRandomSpawnPosition();
                SpawnMiniature(1, position); // Use second prefab as monster
            }
        }

        private Vector3 GetSpawnPosition(int playerIndex)
        {
            var angle = (playerIndex * 360f / maxPlayers) * Mathf.Deg2Rad;
            var x = Mathf.Cos(angle) * spawnRadius;
            var z = Mathf.Sin(angle) * spawnRadius;
            return new Vector3(x, 0.5f, z);
        }

        private Vector3 GetRandomSpawnPosition()
        {
            var angle = Random.Range(0f, 360f) * Mathf.Deg2Rad;
            var radius = Random.Range(1f, spawnRadius);
            var x = Mathf.Cos(angle) * radius;
            var z = Mathf.Sin(angle) * radius;
            return new Vector3(x, 0.5f, z);
        }

        public GameObject SpawnMiniature(int prefabIndex, Vector3 position)
        {
            if (prefabIndex < 0 || prefabIndex >= miniaturePrefabs.Length)
            {
                Debug.LogError("Invalid miniature prefab index!");
                return null;
            }

            var miniature = Instantiate(miniaturePrefabs[prefabIndex], position, Quaternion.identity);
            miniature.transform.localScale = Vector3.one * miniatureScale;
            miniature.layer = LayerMask.NameToLayer("Miniature");

            // Add interaction components
            var rigidbody = miniature.AddComponent<Rigidbody>();
            rigidbody.mass = 1f;
            rigidbody.drag = 0.5f;
            rigidbody.angularDrag = 0.5f;

            var collider = miniature.AddComponent<BoxCollider>();

            var grabInteractable = miniature.AddComponent<XRGrabInteractable>();
            grabInteractable.interactionManager = interactionManager;
            grabInteractable.interactionLayers = InteractionLayerMask.GetMask("Miniature");

            // Add miniature controller
            var controller = miniature.AddComponent<MiniatureController>();
            controller.Initialize(this);

            miniatures.Add(miniature);

            return miniature;
        }

        public void RollDice(int diceType)
        {
            int prefabIndex = GetDicePrefabIndex(diceType);
            if (prefabIndex < 0 || prefabIndex >= dicePrefabs.Length)
            {
                Debug.LogError($"Invalid dice type: {diceType}");
                return;
            }

            var spawnPos = diceSpawnPoint != null ? diceSpawnPoint.position : Vector3.up * 2f;
            var die = Instantiate(dicePrefabs[prefabIndex], spawnPos, Random.rotation);

            // Add physics and interaction
            var rigidbody = die.AddComponent<Rigidbody>();
            rigidbody.mass = 0.1f;
            rigidbody.drag = 0.1f;
            rigidbody.angularDrag = 0.1f;

            // Add random throw force
            var throwDirection = Random.onUnitSphere;
            throwDirection.y = Mathf.Abs(throwDirection.y);
            rigidbody.AddForce(throwDirection * diceThrowForce, ForceMode.Impulse);
            rigidbody.AddTorque(Random.onUnitSphere * 10f, ForceMode.Impulse);

            var collider = die.GetComponent<Collider>();
            if (collider == null)
            {
                collider = die.AddComponent<BoxCollider>();
            }

            var grabInteractable = die.AddComponent<XRGrabInteractable>();
            grabInteractable.interactionManager = interactionManager;
            grabInteractable.interactionLayers = InteractionLayerMask.GetMask("Dice");

            // Add dice controller
            var controller = die.AddComponent<DiceController>();
            controller.Initialize(this, diceType);

            dice.Add(die);

            // Auto-remove dice after 10 seconds
            StartCoroutine(RemoveDiceAfterDelay(die, 10f));
        }

        private int GetDicePrefabIndex(int diceType)
        {
            return diceType switch
            {
                4 => 0,
                6 => 1,
                8 => 2,
                10 => 3,
                12 => 4,
                20 => 5,
                _ => -1
            };
        }

        private IEnumerator RemoveDiceAfterDelay(GameObject die, float delay)
        {
            yield return new WaitForSeconds(delay);

            if (die != null && dice.Contains(die))
            {
                dice.Remove(die);
                Destroy(die);
            }
        }

        private void SetupVRControllers()
        {
            // Find and configure VR controllers
            var controllers = xrRig.GetComponentsInChildren<XRController>();
            foreach (var controller in controllers)
            {
                // Add controller input handlers
                var inputHandler = controller.gameObject.AddComponent<VRControllerInput>();
                inputHandler.Initialize(this);
            }
        }

        private void ConfigureVRCamera()
        {
            // Configure VR camera settings
            var camera = xrRig.cameraGameObject;
            if (camera != null)
            {
                var cam = camera.GetComponent<Camera>();
                if (cam != null)
                {
                    cam.nearClipPlane = 0.1f;
                    cam.farClipPlane = 100f;
                }
            }
        }

        private void SetupARSession()
        {
            // Setup AR session components
            var arSessionOrigin = FindObjectOfType<ARSessionOrigin>();
            if (arSessionOrigin != null)
            {
                // Configure AR session origin
                arSessionOrigin.sessionOrigin.transform.position = Vector3.zero;
            }
        }

        private void ConfigureARCamera()
        {
            // Configure AR camera settings
            var arCamera = Camera.main;
            if (arCamera != null)
            {
                arCamera.nearClipPlane = 0.1f;
                arCamera.farClipPlane = 50f;
            }
        }

        private void InitializeQualitySettings()
        {
            // Set initial quality based on device capabilities
            QualitySettings.SetQualityLevel(GetOptimalQualityLevel(), true);

            if (enableOcclusion)
            {
                Physics.defaultContactOffset = 0.01f;
            }
        }

        private int GetOptimalQualityLevel()
        {
            // Determine optimal quality based on device
            if (SystemInfo.systemMemorySize < 4096)
            {
                return 1; // Low quality
            }
            else if (SystemInfo.systemMemorySize < 8192)
            {
                return 2; // Medium quality
            }
            else
            {
                return 3; // High quality
            }
        }

        private void UpdatePerformanceMetrics()
        {
            frameCount++;
            var currentTime = Time.realtimeSinceStartup;

            if (currentTime - lastFPSTime >= 1f)
            {
                currentFPS = frameCount / (currentTime - lastFPSTime);
                frameCount = 0;
                lastFPSTime = currentTime;

                // Debug.Log($"FPS: {currentFPS:F1}");
            }
        }

        private void AdjustQualityBasedOnPerformance()
        {
            const float minAcceptableFPS = 60f;
            const float targetFPS = 90f;

            if (currentFPS < minAcceptableFPS && currentFPS > 0)
            {
                // Reduce quality
                var currentLevel = QualitySettings.GetQualityLevel();
                if (currentLevel > 0)
                {
                    QualitySettings.DecreaseLevel();
                    Debug.Log($"Decreased quality to level {QualitySettings.GetQualityLevel()} due to low FPS: {currentFPS:F1}");
                    OnPerformanceLevelChanged?.Invoke();
                }
            }
            else if (currentFPS > targetFPS)
            {
                // Can potentially increase quality
                var currentLevel = QualitySettings.GetQualityLevel();
                if (currentLevel < QualitySettings.names.Length - 1)
                {
                    QualitySettings.IncreaseLevel();
                    Debug.Log($"Increased quality to level {QualitySettings.GetQualityLevel()}. FPS: {currentFPS:F1}");
                    OnPerformanceLevelChanged?.Invoke();
                }
            }
        }

        private void HandleInput()
        {
            // Handle keyboard shortcuts for testing
            if (Input.GetKeyDown(KeyCode.Alpha1))
            {
                RollDice(4);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                RollDice(6);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha3))
            {
                RollDice(8);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha4))
            {
                RollDice(10);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha5))
            {
                RollDice(12);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha6))
            {
                RollDice(20);
            }
            else if (Input.GetKeyDown(KeyCode.T))
            {
                SetLightingMode(!GetLightingMode()); // Toggle lighting
            }
        }

        public void SetLightingMode(bool isDungeon)
        {
            if (mainLight != null)
            {
                mainLight.color = isDungeon ? dungeonLightColor : dayLightColor;
                mainLight.intensity = isDungeon ? 0.7f : 1.2f;
            }

            foreach (var light in ambientLights)
            {
                if (light != null)
                {
                    light.intensity = isDungeon ? 0.3f : 0.5f;
                }
            }
        }

        public bool GetLightingMode()
        {
            return mainLight != null && mainLight.color.Equals(dungeonLightColor);
        }

        // Public API methods
        public void AddPlayer(GameObject playerPrefab = null)
        {
            if (players.Count >= maxPlayers)
            {
                Debug.LogWarning("Maximum players reached!");
                return;
            }

            var prefab = playerPrefab ?? this.playerPrefab;
            if (prefab == null)
            {
                Debug.LogError("Player prefab not assigned!");
                return;
            }

            var position = GetSpawnPosition(players.Count);
            var player = Instantiate(prefab, position, Quaternion.identity);

            players.Add(player);
            OnPlayerJoined?.Invoke();
        }

        public void RemoveMiniature(GameObject miniature)
        {
            if (miniatures.Contains(miniature))
            {
                miniatures.Remove(miniature);
                Destroy(miniature);
            }
        }

        public void ClearTabletop()
        {
            // Remove all miniatures
            foreach (var miniature in miniatures)
            {
                Destroy(miniature);
            }
            miniatures.Clear();

            // Remove all dice
            foreach (var die in dice)
            {
                Destroy(die);
            }
            dice.Clear();

            // Remove all players
            foreach (var player in players)
            {
                Destroy(player);
            }
            players.Clear();
        }

        public void ResetTabletop()
        {
            ClearTabletop();
            SpawnInitialMiniatures();
        }

        // Getters
        public bool IsVRActive => isVRActive;
        public bool IsARActive => isARActive;
        public bool IsInitialized => isInitialized;
        public float CurrentFPS => currentFPS;
        public int PlayerCount => players.Count;
        public int MiniatureCount => miniatures.Count;
        public GameObject TabletopInstance => tabletopInstance;
        public List<GameObject> Miniatures => new List<GameObject>(miniatures);

        private void OnDestroy()
        {
            // Cleanup
            ClearTabletop();

            if (tabletopInstance != null)
            {
                Destroy(tabletopInstance);
            }

            // Stop XR subsystems
            var xrManager = XRGeneralSettings.Instance.Manager;
            if (xrManager != null)
            {
                xrManager.StopSubsystems();
                xrManager.DeinitializeLoader();
            }
        }

        private void OnGUI()
        {
            if (!isInitialized) return;

            // Simple GUI for debugging
            GUILayout.BeginArea(new Rect(10, 10, 300, 200));
            GUILayout.Label($"FPS: {currentFPS:F1}");
            GUILayout.Label($"Players: {players.Count}");
            GUILayout.Label($"Miniatures: {miniatures.Count}");
            GUILayout.Label($"Dice: {dice.Count}");
            GUILayout.Label($"Quality: {QualitySettings.names[QualitySettings.GetQualityLevel()]}");
            GUILayout.Label($"VR Active: {isVRActive}");
            GUILayout.Label($"AR Active: {isARActive}");

            GUILayout.Space(10);

            if (GUILayout.Button("Roll d20"))
            {
                RollDice(20);
            }

            if (GUILayout.Button("Toggle Lighting"))
            {
                SetLightingMode(!GetLightingMode());
            }

            if (GUILayout.Button("Reset Tabletop"))
            {
                ResetTabletop();
            }

            GUILayout.EndArea();
        }
    }
}