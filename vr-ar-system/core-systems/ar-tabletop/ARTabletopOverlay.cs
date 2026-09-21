using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using System.Collections.Generic;
using System.Collections;
using System.Linq;

namespace DMLog.VR
{
    /// <summary>
    /// Revolutionary AR Tabletop Overlay System
    /// Projects digital elements onto real tables with smart surface detection
    /// </summary>
    public class ARTabletopOverlay : MonoBehaviour
    {
        [Header("AR Foundation Components")]
        [SerializeField] private ARSession arSession;
        [SerializeField] private ARSessionOrigin arSessionOrigin;
        [SerializeField] private ARPlaneManager planeManager;
        [SerializeField] private ARPointCloudManager pointCloudManager;
        [SerializeField] private AROcclusionManager occlusionManager;

        [Header("Table Detection")]
        [SerializeField] private float minTableArea = 0.5f; // Minimum table surface area in square meters
        [SerializeField] private float maxTableArea = 4.0f; // Maximum table surface area
        [SerializeField] private float tableHeightThreshold = 1.2f; // Maximum height for table detection
        [SerializeField] private LayerMask tableDetectionLayer = -1;
        [SerializeField] private bool enableSmartSurfaceDetection = true;

        [Header("Overlay Content")]
        [SerializeField] private GameObject virtualTabletopPrefab;
        [SerializeField] private GameObject gridOverlayPrefab;
        [SerializeField] private GameObject diceRollerPrefab;
        [SerializeField] private GameObject characterTokenPrefab;
        [SerializeField] private GameObject environmentEffectPrefab;

        [Header("Interaction Settings")]
        [SerializeField] private bool enableTouchInteraction = true;
        [SerializeField] private bool enableGestureInteraction = true;
        [SerializeField] private float touchSensitivity = 0.1f;
        [SerializeField] private float gestureThreshold = 0.5f;

        [Header("Visual Settings")]
        [SerializeField] private Material tableMaterial;
        [SerializeField] private Material gridMaterial;
        [SerializeField] private float gridOpacity = 0.3f;
        [SerializeField] private Color gridColor = Color.white;
        [SerializeField] private bool showTableBoundaries = true;

        [Header("Performance Settings")]
        [SerializeField] private int maxPointCloudPoints = 1000;
        [SerializeField] private float updateFrequency = 30f;
        [SerializeField] private bool enableOcclusion = true;

        // Private state
        private ARPlane detectedTable = null;
        private GameObject virtualTabletop = null;
        private GameObject gridOverlay = null;
        private List<GameObject> activeTokens = new List<GameObject>();
        private List<GameObject> activeEffects = new List<GameObject>();
        private Camera arCamera;
        private Vector2 touchStartPosition;
        private bool isTouching = false;
        private float lastUpdateTime = 0f;
        private TableDetectionState detectionState = TableDetectionState.Searching;

        // Events
        public System.Action<ARPlane> OnTableDetected;
        public System.Action<Vector3> OnTabletopTapped;
        public System.Action<GameObject> OnTokenPlaced;
        public System.Action<int> OnDiceRolled;
        public System.Action<TableDetectionState> OnDetectionStateChanged;

        public enum TableDetectionState
        {
            Searching, Detected, Tracking, Lost
        }

        [System.Serializable]
        public class TokenData
        {
            public string tokenId;
            public string characterName;
            public Vector3 localPosition;
            public Quaternion localRotation;
            public CharacterRole role;
            public GameObject tokenInstance;
        }

        public enum CharacterRole
        {
            Player, NPC, Enemy, Object
        }

        private void Awake()
        {
            InitializeARSystem();
        }

        private void Start()
        {
            SetupARComponents();
            StartTableDetection();
        }

        private void Update()
        {
            HandleInput();
            UpdateTableTracking();
            UpdateARPerformance();
        }

        /// <summary>
        /// Initialize AR system components
        /// </summary>
        private void InitializeARSystem()
        {
            Debug.Log("Initializing AR Tabletop Overlay System");

            // Get AR camera
            arCamera = Camera.main;
            if (arCamera == null)
            {
                arCamera = FindObjectOfType<Camera>();
            }

            // Set up AR session
            if (arSession == null)
            {
                arSession = FindObjectOfType<ARSession>();
            }

            Debug.Log("AR Tabletop Overlay System initialized");
        }

        /// <summary>
        /// Setup AR Foundation components
        /// </summary>
        private void SetupARComponents()
        {
            // Configure plane manager
            if (planeManager != null)
            {
                planeManager.planesChanged += OnPlanesChanged;

                // Configure plane detection for horizontal surfaces only
                planeManager.requestedDetectionMode = PlaneDetectionMode.Horizontal;
            }

            // Configure point cloud manager
            if (pointCloudManager != null)
            {
                pointCloudManager.pointCloudsChanged += OnPointCloudsChanged;
            }

            // Configure occlusion manager
            if (occlusionManager != null)
            {
                occlusionManager.enabled = enableOcclusion;
            }

            Debug.Log("AR components configured");
        }

        /// <summary>
        /// Start table detection process
        /// </summary>
        private void StartTableDetection()
        {
            Debug.Log("Starting table detection...");
            detectionState = TableDetectionState.Searching;
            OnDetectionStateChanged?.Invoke(detectionState);

            // Start scanning for tables
            StartCoroutine(TableDetectionRoutine());
        }

        /// <summary>
        /// Table detection coroutine
        /// </summary>
        private IEnumerator TableDetectionRoutine()
        {
            while (detectionState == TableDetectionState.Searching)
            {
                // Check for suitable planes
                if (planeManager != null)
                {
                    var horizontalPlanes = planeManager.trackables
                        .Where(plane => plane.alignment == PlaneAlignment.HorizontalUp)
                        .ToList();

                    foreach (var plane in horizontalPlanes)
                    {
                        if (IsSuitableTable(plane))
                        {
                            OnTableFound(plane);
                            yield break;
                        }
                    }
                }

                yield return new WaitForSeconds(0.5f);
            }
        }

        /// <summary>
        /// Check if a plane is suitable as a table surface
        /// </summary>
        private bool IsSuitableTable(ARPlane plane)
        {
            if (!enableSmartSurfaceDetection) return true;

            // Check if plane is within size constraints
            Vector2 planeSize = plane.size;
            float area = planeSize.x * planeSize.y;

            if (area < minTableArea || area > maxTableArea)
            {
                return false;
            }

            // Check if plane is at appropriate height
            Vector3 planePosition = plane.transform.position;
            if (planePosition.y > tableHeightThreshold)
            {
                return false;
            }

            // Check plane stability (has been tracked for sufficient time)
            if (plane.trackingState != TrackingState.Tracking)
            {
                return false;
            }

            // Check if plane is sufficiently flat
            if (!IsPlaneFlat(plane))
            {
                return false;
            }

            return true;
        }

        /// <summary>
        /// Check if plane surface is sufficiently flat
        /// </summary>
        private bool IsPlaneFlat(ARPlane plane)
        {
            // Get boundary vertices
            var boundary = plane.boundary;
            if (boundary.Length < 3) return false;

            // Calculate plane normal variance
            Vector3 planeNormal = plane.normal;
            float maxVariance = 0f;

            for (int i = 0; i < boundary.Length - 2; i++)
            {
                Vector3 v1 = boundary[i];
                Vector3 v2 = boundary[i + 1];
                Vector3 v3 = boundary[i + 2];

                Vector3 triangleNormal = Vector3.Cross(v2 - v1, v3 - v1).normalized;
                float variance = Vector3.Angle(planeNormal, triangleNormal);

                maxVariance = Mathf.Max(maxVariance, variance);
            }

            // Plane is flat if variance is less than 15 degrees
            return maxVariance < 15f;
        }

        /// <summary>
        /// Handle detected table
        /// </summary>
        private void OnTableFound(ARPlane plane)
        {
            Debug.Log($"Table detected: {plane.trackableId}");
            detectedTable = plane;
            detectionState = TableDetectionState.Detected;
            OnDetectionStateChanged?.Invoke(detectionState);
            OnTableDetected?.Invoke(plane);

            // Stop detecting other planes
            if (planeManager != null)
            {
                planeManager.requestedDetectionMode = PlaneDetectionMode.None;
            }

            // Create virtual tabletop overlay
            CreateVirtualTabletop(plane);
        }

        /// <summary>
        /// Create virtual tabletop overlay
        /// </summary>
        private void CreateVirtualTabletop(ARPlane plane)
        {
            // Remove existing tabletop
            if (virtualTabletop != null)
            {
                Destroy(virtualTabletop);
            }

            // Create new virtual tabletop
            virtualTabletop = Instantiate(virtualTabletopPrefab, plane.transform);
            virtualTabletop.name = "VirtualTabletop";

            // Position and scale to match detected table
            Vector2 planeSize = plane.size;
            virtualTabletop.transform.localScale = new Vector3(planeSize.x, 1f, planeSize.y);
            virtualTabletop.transform.localPosition = Vector3.zero;

            // Apply table material
            var renderer = virtualTabletop.GetComponent<Renderer>();
            if (renderer != null && tableMaterial != null)
            {
                renderer.material = tableMaterial;
            }

            // Create grid overlay
            CreateGridOverlay(plane);

            // Add interaction components
            AddTabletopInteraction();

            Debug.Log("Virtual tabletop created");
        }

        /// <summary>
        /// Create grid overlay on the tabletop
        /// </summary>
        private void CreateGridOverlay(ARPlane plane)
        {
            if (gridOverlayPrefab == null) return;

            // Remove existing grid
            if (gridOverlay != null)
            {
                Destroy(gridOverlay);
            }

            // Create grid overlay
            gridOverlay = Instantiate(gridOverlayPrefab, plane.transform);
            gridOverlay.name = "GridOverlay";

            // Scale grid to match table
            Vector2 planeSize = plane.size;
            gridOverlay.transform.localScale = new Vector3(planeSize.x, 1f, planeSize.y);

            // Configure grid material
            var renderer = gridOverlay.GetComponent<Renderer>();
            if (renderer != null && gridMaterial != null)
            {
                var material = new Material(gridMaterial);
                material.color = new Color(gridColor.r, gridColor.g, gridColor.b, gridOpacity);
                renderer.material = material;
            }

            Debug.Log("Grid overlay created");
        }

        /// <summary>
        /// Add interaction components to tabletop
        /// </summary>
        private void AddTabletopInteraction()
        {
            if (virtualTabletop == null) return;

            // Add collider for interaction
            var collider = virtualTabletop.GetComponent<Collider>();
            if (collider == null)
            {
                collider = virtualTabletop.AddComponent<BoxCollider>();
            }

            // Add AR interaction components
            var arInteractable = virtualTabletop.AddComponent<ARRaycastHit>();
            var arTouchHandler = virtualTabletop.AddComponent<ARTouchHandler>();

            // Configure touch handler
            arTouchHandler.OnTouchBegan += HandleTabletopTouch;
            arTouchHandler.OnTouchMoved += HandleTabletopDrag;
            arTouchHandler.OnTouchEnded += HandleTabletopRelease;
        }

        /// <summary>
        /// Handle touch input on tabletop
        /// </summary>
        private void HandleInput()
        {
            if (!enableTouchInteraction) return;

            // Handle touch input
            if (Input.touchCount > 0)
            {
                Touch touch = Input.GetTouch(0);

                switch (touch.phase)
                {
                    case TouchPhase.Began:
                        OnTouchBegan(touch.position);
                        break;
                    case TouchPhase.Moved:
                        OnTouchMoved(touch.position);
                        break;
                    case TouchPhase.Ended:
                        OnTouchEnded(touch.position);
                        break;
                }
            }

            // Handle mouse input for testing
            if (Application.isEditor)
            {
                if (Input.GetMouseButtonDown(0))
                {
                    OnTouchBegan(Input.mousePosition);
                }
                else if (Input.GetMouseButton(0))
                {
                    OnTouchMoved(Input.mousePosition);
                }
                else if (Input.GetMouseButtonUp(0))
                {
                    OnTouchEnded(Input.mousePosition);
                }
            }
        }

        /// <summary>
        /// Handle touch began
        /// </summary>
        private void OnTouchBegan(Vector2 screenPosition)
        {
            touchStartPosition = screenPosition;
            isTouching = true;

            // Perform AR raycast
            if (arSessionOrigin != null)
            {
                Ray ray = arCamera.ScreenPointToRay(screenPosition);
                RaycastHit hit;

                if (Physics.Raycast(ray, out hit, 10f))
                {
                    HandleTabletopTouch(hit.point);
                }
            }
        }

        /// <summary>
        /// Handle touch moved
        /// </summary>
        private void OnTouchMoved(Vector2 screenPosition)
        {
            if (!isTouching) return;

            // Calculate drag distance
            float dragDistance = Vector2.Distance(screenPosition, touchStartPosition);

            if (dragDistance > touchSensitivity)
            {
                // Perform AR raycast for drag
                if (arSessionOrigin != null)
                {
                    Ray ray = arCamera.ScreenPointToRay(screenPosition);
                    RaycastHit hit;

                    if (Physics.Raycast(ray, out hit, 10f))
                    {
                        HandleTabletopDrag(hit.point);
                    }
                }
            }
        }

        /// <summary>
        /// Handle touch ended
        /// </summary>
        private void OnTouchEnded(Vector2 screenPosition)
        {
            isTouching = false;

            // Check for tap gesture (no significant movement)
            float dragDistance = Vector2.Distance(screenPosition, touchStartPosition);
            if (dragDistance < touchSensitivity)
            {
                // Perform AR raycast for tap
                if (arSessionOrigin != null)
                {
                    Ray ray = arCamera.ScreenPointToRay(screenPosition);
                    RaycastHit hit;

                    if (Physics.Raycast(ray, out hit, 10f))
                    {
                        HandleTabletopTap(hit.point);
                    }
                }
            }

            HandleTabletopRelease(screenPosition);
        }

        /// <summary>
        /// Handle tabletop touch
        /// </summary>
        private void HandleTabletopTouch(Vector3 worldPosition)
        {
            Debug.Log($"Tabletop touched at: {worldPosition}");
        }

        /// <summary>
        /// Handle tabletop drag
        /// </summary>
        private void HandleTabletopDrag(Vector3 worldPosition)
        {
            // Handle dragging of tokens or other objects
            Debug.Log($"Tabletop dragged at: {worldPosition}");
        }

        /// <summary>
        /// Handle tabletop tap
        /// </summary>
        private void HandleTabletopTap(Vector3 worldPosition)
        {
            Debug.Log($"Tabletop tapped at: {worldPosition}");
            OnTabletopTapped?.Invoke(worldPosition);

            // Create tap effect
            CreateTapEffect(worldPosition);
        }

        /// <summary>
        /// Handle tabletop release
        /// </summary>
        private void HandleTabletopRelease(Vector2 screenPosition)
        {
            Debug.Log($"Tabletop released at: {screenPosition}");
        }

        /// <summary>
        /// Create visual effect for tap
        /// </summary>
        private void CreateTapEffect(Vector3 position)
        {
            // Create a simple effect at tap position
            var effect = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            effect.name = "TapEffect";
            effect.transform.position = position;
            effect.transform.localScale = Vector3.one * 0.1f;

            var renderer = effect.GetComponent<Renderer>();
            var material = new Material(Shader.Find("Standard"));
            material.color = Color.white;
            renderer.material = material;

            // Animate and destroy
            StartCoroutine(AnimateTapEffect(effect));
        }

        /// <summary>
        /// Animate tap effect
        /// </summary>
        private IEnumerator AnimateTapEffect(GameObject effect)
        {
            Vector3 startScale = effect.transform.localScale;
            Vector3 targetScale = startScale * 2f;
            float duration = 0.5f;
            float elapsed = 0f;

            var renderer = effect.GetComponent<Renderer>();
            var material = renderer.material;
            Color startColor = material.color;
            Color targetColor = new Color(startColor.r, startColor.g, startColor.b, 0f);

            while (elapsed < duration)
            {
                float t = elapsed / duration;
                effect.transform.localScale = Vector3.Lerp(startScale, targetScale, t);
                material.color = Color.Lerp(startColor, targetColor, t);
                elapsed += Time.deltaTime;
                yield return null;
            }

            Destroy(effect);
        }

        /// <summary>
        /// Place character token on tabletop
        /// </summary>
        public GameObject PlaceToken(Vector3 worldPosition, string characterName, CharacterRole role = CharacterRole.Player)
        {
            if (detectedTable == null)
            {
                Debug.LogWarning("No table detected");
                return null;
            }

            // Create token
            var token = Instantiate(characterTokenPrefab, detectedTable.transform);
            token.name = $"Token_{characterName}";

            // Position token
            Vector3 localPosition = detectedTable.transform.InverseTransformPoint(worldPosition);
            token.transform.localPosition = localPosition;
            token.transform.localPosition = new Vector3(localPosition.x, 0.01f, localPosition.z); // Slightly above table

            // Configure token
            var tokenComponent = token.AddComponent<CharacterToken>();
            tokenComponent.characterName = characterName;
            tokenComponent.role = role;

            // Set token appearance based on role
            SetTokenAppearance(token, role);

            activeTokens.Add(token);
            OnTokenPlaced?.Invoke(token);

            Debug.Log($"Token placed: {characterName} at {worldPosition}");
            return token;
        }

        /// <summary>
        /// Set token appearance based on role
        /// </summary>
        private void SetTokenAppearance(GameObject token, CharacterRole role)
        {
            var renderer = token.GetComponent<Renderer>();
            if (renderer == null) return;

            Material material = new Material(Shader.Find("Standard"));

            switch (role)
            {
                case CharacterRole.Player:
                    material.color = Color.blue;
                    break;
                case CharacterRole.NPC:
                    material.color = Color.green;
                    break;
                case CharacterRole.Enemy:
                    material.color = Color.red;
                    break;
                case CharacterRole.Object:
                    material.color = Color.gray;
                    break;
            }

            renderer.material = material;
        }

        /// <summary>
        /// Roll dice on tabletop
        /// </summary>
        public void RollDice(int sides, Vector3 worldPosition)
        {
            if (detectedTable == null) return;

            // Create dice roller
            var diceRoller = Instantiate(diceRollerPrefab, detectedTable.transform);
            diceRoller.name = $"DiceRoller_{sides}sided";

            // Position dice
            Vector3 localPosition = detectedTable.transform.InverseTransformPoint(worldPosition);
            diceRoller.transform.localPosition = new Vector3(localPosition.x, 0.05f, localPosition.z);

            // Configure dice
            var diceComponent = diceRoller.AddComponent<DiceRoller>();
            diceComponent.sides = sides;
            diceComponent.onRollComplete = (int result) => {
                OnDiceRolled?.Invoke(result);
                Destroy(diceRoller, 3f); // Clean up after 3 seconds
            };

            // Roll the dice
            diceComponent.Roll();

            Debug.Log($"Dice rolled: {sides} sides at {worldPosition}");
        }

        /// <summary>
        /// Create environmental effect
        /// </summary>
        public void CreateEnvironmentEffect(string effectName, Vector3 worldPosition)
        {
            if (detectedTable == null) return;

            // Create effect
            var effect = Instantiate(environmentEffectPrefab, detectedTable.transform);
            effect.name = $"Effect_{effectName}";

            // Position effect
            Vector3 localPosition = detectedTable.transform.InverseTransformPoint(worldPosition);
            effect.transform.localPosition = new Vector3(localPosition.x, 0.02f, localPosition.z);

            // Configure effect
            var effectComponent = effect.AddComponent<EnvironmentEffect>();
            effectComponent.effectName = effectName;
            effectComponent.onEffectComplete = () => {
                activeEffects.Remove(effect);
                Destroy(effect);
            };

            // Play effect
            effectComponent.Play();

            activeEffects.Add(effect);
            Debug.Log($"Environment effect created: {effectName} at {worldPosition}");
        }

        /// <summary>
        /// Handle planes changed event
        /// </summary>
        private void OnPlanesChanged(ARPlanesChangedEventArgs args)
        {
            // Handle new planes
            foreach (var plane in args.added)
            {
                if (detectionState == TableDetectionState.Searching &&
                    plane.alignment == PlaneAlignment.HorizontalUp)
                {
                    if (IsSuitableTable(plane))
                    {
                        OnTableFound(plane);
                        break;
                    }
                }
            }

            // Handle updated planes
            foreach (var plane in args.updated)
            {
                if (detectedTable == plane)
                {
                    UpdateTableTracking(plane);
                }
            }

            // Handle removed planes
            foreach (var plane in args.removed)
            {
                if (detectedTable == plane)
                {
                    OnTableLost();
                }
            }
        }

        /// <summary>
        /// Handle point clouds changed event
        /// </summary>
        private void OnPointCloudsChanged(ARPointCloudsChangedEventArgs args)
        {
            // Limit point cloud for performance
            if (pointCloudManager != null)
            {
                foreach (var pointCloud in pointCloudManager.trackables)
                {
                    var renderer = pointCloud.GetComponent<Renderer>();
                    if (renderer != null)
                    {
                        // Limit point cloud density
                        // Implementation depends on specific point cloud system
                    }
                }
            }
        }

        /// <summary>
        /// Update table tracking
        /// </summary>
        private void UpdateTableTracking()
        {
            if (detectedTable == null) return;

            // Update tracking state
            if (detectedTable.trackingState == TrackingState.Tracking)
            {
                if (detectionState != TableDetectionState.Tracking)
                {
                    detectionState = TableDetectionState.Tracking;
                    OnDetectionStateChanged?.Invoke(detectionState);
                }
            }
            else
            {
                if (detectionState == TableDetectionState.Tracking)
                {
                    detectionState = TableDetectionState.Lost;
                    OnDetectionStateChanged?.Invoke(detectionState);
                }
            }
        }

        /// <summary>
        /// Update table tracking for specific plane
        /// </summary>
        private void UpdateTableTracking(ARPlane plane)
        {
            // Update virtual tabletop position and scale
            if (virtualTabletop != null && plane == detectedTable)
            {
                Vector2 planeSize = plane.size;
                virtualTabletop.transform.localScale = new Vector3(planeSize.x, 1f, planeSize.y);
            }

            // Update grid overlay
            if (gridOverlay != null && plane == detectedTable)
            {
                Vector2 planeSize = plane.size;
                gridOverlay.transform.localScale = new Vector3(planeSize.x, 1f, planeSize.y);
            }
        }

        /// <summary>
        /// Handle table lost
        /// </summary>
        private void OnTableLost()
        {
            Debug.LogWarning("Table lost - restarting detection");
            detectedTable = null;
            detectionState = TableDetectionState.Searching;
            OnDetectionStateChanged?.Invoke(detectionState);

            // Clean up virtual tabletop
            if (virtualTabletop != null)
            {
                Destroy(virtualTabletop);
                virtualTabletop = null;
            }

            if (gridOverlay != null)
            {
                Destroy(gridOverlay);
                gridOverlay = null;
            }

            // Restart table detection
            StartTableDetection();
        }

        /// <summary>
        /// Update AR performance settings
        /// </summary>
        private void UpdateARPerformance()
        {
            if (Time.time - lastUpdateTime < (1f / updateFrequency)) return;

            lastUpdateTime = Time.time;

            // Adjust quality based on performance
            float currentFPS = 1f / Time.unscaledDeltaTime;

            if (currentFPS < 30f)
            {
                // Reduce quality
                if (pointCloudManager != null)
                {
                    pointCloudManager.enabled = false;
                }
            }
            else if (currentFPS > 50f)
            {
                // Increase quality
                if (pointCloudManager != null)
                {
                    pointCloudManager.enabled = true;
                }
            }
        }

        /// <summary>
        /// Clear all tokens from tabletop
        /// </summary>
        public void ClearTokens()
        {
            foreach (var token in activeTokens)
            {
                if (token != null)
                {
                    Destroy(token);
                }
            }
            activeTokens.Clear();
        }

        /// <summary>
        /// Clear all effects from tabletop
        /// </summary>
        public void ClearEffects()
        {
            foreach (var effect in activeEffects)
            {
                if (effect != null)
                {
                    Destroy(effect);
                }
            }
            activeEffects.Clear();
        }

        /// <summary>
        /// Get current table detection state
        /// </summary>
        public TableDetectionState GetDetectionState()
        {
            return detectionState;
        }

        /// <summary>
        /// Get detected table plane
        /// </summary>
        public ARPlane GetDetectedTable()
        {
            return detectedTable;
        }

        private void OnDestroy()
        {
            // Cleanup AR components
            if (planeManager != null)
            {
                planeManager.planesChanged -= OnPlanesChanged;
            }

            if (pointCloudManager != null)
            {
                pointCloudManager.pointCloudsChanged -= OnPointCloudsChanged;
            }

            // Cleanup virtual objects
            if (virtualTabletop != null)
            {
                Destroy(virtualTabletop);
            }

            if (gridOverlay != null)
            {
                Destroy(gridOverlay);
            }

            ClearTokens();
            ClearEffects();
        }
    }

    /// <summary>
    /// Character token component
    /// </summary>
    public class CharacterToken : MonoBehaviour
    {
        public string characterName;
        public ARTabletopOverlay.CharacterRole role;
        public bool isSelected = false;
    }

    /// <summary>
    /// Dice roller component
    /// </summary>
    public class DiceRoller : MonoBehaviour
    {
        public int sides = 20;
        public System.Action<int> onRollComplete;

        public void Roll()
        {
            StartCoroutine(RollCoroutine());
        }

        private IEnumerator RollCoroutine()
        {
            // Simulate dice rolling animation
            float duration = 2f;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                // Rotate dice
                transform.Rotate(Random.Range(-180f, 180f), Random.Range(-180f, 180f), Random.Range(-180f, 180f));
                elapsed += Time.deltaTime;
                yield return null;
            }

            // Determine result
            int result = Random.Range(1, sides + 1);

            // Stop on result face
            // Set rotation to show result (simplified)
            transform.rotation = Quaternion.identity;

            // Callback
            onRollComplete?.Invoke(result);
        }
    }

    /// <summary>
    /// Environment effect component
    /// </summary>
    public class EnvironmentEffect : MonoBehaviour
    {
        public string effectName;
        public System.Action onEffectComplete;

        public void Play()
        {
            StartCoroutine(PlayEffect());
        }

        private IEnumerator PlayEffect()
        {
            // Play effect animation
            float duration = 3f;
            float elapsed = 0f;

            var renderer = GetComponent<Renderer>();
            var material = renderer.material;
            Color startColor = material.color;
            Color targetColor = new Color(startColor.r, startColor.g, startColor.b, 0f);

            while (elapsed < duration)
            {
                float t = elapsed / duration;
                material.color = Color.Lerp(startColor, targetColor, t);
                elapsed += Time.deltaTime;
                yield return null;
            }

            onEffectComplete?.Invoke();
        }
    }

    /// <summary>
    /// AR touch handler component
    /// </summary>
    public class ARTouchHandler : MonoBehaviour
    {
        public System.Action<Vector3> OnTouchBegan;
        public System.Action<Vector3> OnTouchMoved;
        public System.Action<Vector2> OnTouchEnded;

        private void OnMouseDown()
        {
            Vector3 worldPosition = GetWorldPositionFromMouse();
            OnTouchBegan?.Invoke(worldPosition);
        }

        private void OnMouseDrag()
        {
            Vector3 worldPosition = GetWorldPositionFromMouse();
            OnTouchMoved?.Invoke(worldPosition);
        }

        private void OnMouseUp()
        {
            OnTouchEnded?.Invoke(Input.mousePosition);
        }

        private Vector3 GetWorldPositionFromMouse()
        {
            Vector3 mousePosition = Input.mousePosition;
            Camera camera = Camera.main;
            Vector3 worldPosition = camera.ScreenToWorldPoint(new Vector3(mousePosition.x, mousePosition.y, camera.nearClipPlane));
            return worldPosition;
        }
    }
}