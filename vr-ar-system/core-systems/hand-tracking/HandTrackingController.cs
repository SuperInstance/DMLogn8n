using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;
using System.Collections.Generic;
using System.Linq;
using Unity.Collections;
using Unity.XR.CoreUtils;

namespace DMLog.VR
{
    /// <summary>
    /// Advanced Hand Tracking System for Natural VR Interaction
    /// Supports gesture recognition, physics interaction, and haptic feedback
    /// </summary>
    public class HandTrackingController : MonoBehaviour
    {
        [Header("Hand Configuration")]
        [SerializeField] private XRNode handSide = XRNode.RightHand;
        [SerializeField] private bool enableHandTracking = true;
        [SerializeField] private float handTrackingSensitivity = 1.0f;
        [SerializeField] private bool showDebugVisualization = false;

        [Header("Hand Model")]
        [SerializeField] private GameObject handModelPrefab;
        [SerializeField] private Transform handModelParent;
        [SerializeField] private SkinnedMeshRenderer handRenderer;

        [Header("Interaction Settings")]
        [SerializeField] private float grabStrength = 0.8f;
        [SerializeField] private float pinchThreshold = 0.7f;
        [SerializeField] private float gestureConfidenceThreshold = 0.6f;
        [SerializeField] private LayerMask interactionLayers = -1;

        [Header("Haptic Feedback")]
        [SerializeField] private bool enableHaptics = true;
        [SerializeField] private float hapticAmplitude = 0.5f;
        [SerializeField] private float hapticDuration = 0.1f;

        [Header("Gesture Recognition")]
        [SerializeField] private List<GestureDefinition> customGestures = new List<GestureDefinition>();

        // Private state
        private XRDirectInteractor directInteractor;
        private XRGrabInteractable grabbedObject;
        private Dictionary<string, float> currentGestureValues = new Dictionary<string, float>();
        private HandTrackingDataSource handTrackingData;
        private bool isHandTrackingActive = false;
        private Vector3 lastHandPosition;
        private Quaternion lastHandRotation;

        // Finger tracking data
        private Dictionary<FingerType, FingerTrackingData> fingerData = new Dictionary<FingerType, FingerTrackingData>();

        // Events
        public System.Action<string, Vector3, Quaternion> OnGestureDetected;
        public System.Action<GameObject> OnObjectGrabbed;
        public System.Action<GameObject> OnObjectReleased;
        public System.Action<Vector3> OnHandTracked;
        public System.Action<float> OnHapticTrigger;

        public enum FingerType
        {
            Thumb, Index, Middle, Ring, Pinky
        }

        [System.Serializable]
        public class FingerTrackingData
        {
            public float curl; // 0 = straight, 1 = fully curled
            public float splay; // 0 = closed, 1 = spread
            public Vector3 tipPosition;
            public Quaternion tipRotation;
            public bool isTracking;
        }

        [System.Serializable]
        public class GestureDefinition
        {
            public string gestureName;
            public GestureType type;
            public float[] fingerCurlPattern;
            public float[] fingerSplayPattern;
            public Vector3 handOrientation;
            public bool requireSteadyHand = false;
            public float steadyHandThreshold = 0.1f;
            public float minHoldTime = 0.5f;
        }

        public enum GestureType
        {
            DiceRoll, SpellCast, MiniatureSelect, Point, ThumbsUp, PeaceSign, Rock, Paper, Scissors, Custom
        }

        private void Awake()
        {
            InitializeHandTracking();
        }

        private void Start()
        {
            SetupInteractionSystem();
            InitializeGestures();
            RegisterEventListeners();
        }

        private void Update()
        {
            UpdateHandTracking();
            UpdateFingerTracking();
            ProcessGestures();
            UpdateInteractionFeedback();
        }

        /// <summary>
        /// Initialize hand tracking system
        /// </summary>
        private void InitializeHandTracking()
        {
            Debug.Log($"Initializing Hand Tracking for {handSide}");

            // Get XR Direct Interactor
            directInteractor = GetComponent<XRDirectInteractor>();
            if (directInteractor == null)
            {
                directInteractor = gameObject.AddComponent<XRDirectInteractor>();
            }

            // Initialize hand tracking data source
            handTrackingData = new HandTrackingDataSource(handSide);

            // Initialize finger tracking data
            foreach (FingerType finger in System.Enum.GetValues(typeof(FingerType)))
            {
                fingerData[finger] = new FingerTrackingData
                {
                    curl = 0f,
                    splay = 0f,
                    tipPosition = Vector3.zero,
                    tipRotation = Quaternion.identity,
                    isTracking = false
                };
            }

            // Create hand model if not assigned
            if (handModelPrefab != null && handModelParent == null)
            {
                var handModel = Instantiate(handModelPrefab, transform);
                handModelParent = handModel.transform;
                handRenderer = handModel.GetComponentInChildren<SkinnedMeshRenderer>();

                if (handRenderer != null)
                {
                    handRenderer.updateWhenOffscreen = true;
                }
            }

            Debug.Log("Hand Tracking initialization complete");
        }

        /// <summary>
        /// Setup interaction system components
        /// </summary>
        private void SetupInteractionSystem()
        {
            // Configure direct interactor
            if (directInteractor != null)
            {
                directInteractor.attachTransform = transform;
                directInteractor.hideControllerOnSelect = true;
            }

            // Add haptic capabilities
            var hapticAction = GetComponentInChildren<XRControllerHaptic>();
            if (hapticAction == null && enableHaptics)
            {
                // Add haptic feedback capability
                var hapticGameObject = new GameObject("HapticFeedback");
                hapticGameObject.transform.SetParent(transform);
                // Note: Actual haptic implementation depends on XR SDK
            }
        }

        /// <summary>
        /// Initialize gesture recognition system
        /// </summary>
        private void InitializeGestures()
        {
            // Add default gestures if none are configured
            if (customGestures.Count == 0)
            {
                AddDefaultGestures();
            }

            // Initialize gesture tracking values
            foreach (var gesture in customGestures)
            {
                currentGestureValues[gesture.gestureName] = 0f;
            }

            Debug.Log($"Initialized {customGestures.Count} gestures");
        }

        /// <summary>
        /// Add default gesture definitions
        /// </summary>
        private void AddDefaultGestures()
        {
            // Dice Roll Gesture - Fist with wrist flick
            customGestures.Add(new GestureDefinition
            {
                gestureName = "DiceRoll",
                type = GestureType.DiceRoll,
                fingerCurlPattern = new float[] { 0.9f, 0.9f, 0.9f, 0.9f, 0.9f }, // All fingers curled
                fingerSplayPattern = new float[] { 0.1f, 0.1f, 0.1f, 0.1f, 0.1f },
                handOrientation = Vector3.down,
                minHoldTime = 0.1f
            });

            // Point Gesture - Index finger extended
            customGestures.Add(new GestureDefinition
            {
                gestureName = "Point",
                type = GestureType.Point,
                fingerCurlPattern = new float[] { 0.3f, 0.1f, 0.8f, 0.8f, 0.8f }, // Index extended
                fingerSplayPattern = new float[] { 0.5f, 0.2f, 0.1f, 0.1f, 0.1f },
                handOrientation = Vector3.forward,
                minHoldTime = 0.3f
            });

            // Spell Cast Gesture - Open hand with dramatic motion
            customGestures.Add(new GestureDefinition
            {
                gestureName = "SpellCast",
                type = GestureType.SpellCast,
                fingerCurlPattern = new float[] { 0.2f, 0.2f, 0.2f, 0.2f, 0.2f }, // Open hand
                fingerSplayPattern = new float[] { 0.8f, 0.8f, 0.8f, 0.8f, 0.8f },
                handOrientation = Vector3.up,
                requireSteadyHand = true,
                steadyHandThreshold = 0.2f,
                minHoldTime = 1.0f
            });

            // Thumbs Up Gesture
            customGestures.Add(new GestureDefinition
            {
                gestureName = "ThumbsUp",
                type = GestureType.ThumbsUp,
                fingerCurlPattern = new float[] { 0.1f, 0.9f, 0.9f, 0.9f, 0.9f }, // Thumb up
                fingerSplayPattern = new float[] { 0.2f, 0.1f, 0.1f, 0.1f, 0.1f },
                handOrientation = Vector3.up,
                minHoldTime = 0.5f
            });
        }

        /// <summary>
        /// Register event listeners
        /// </summary>
        private void RegisterEventListeners()
        {
            if (directInteractor != null)
            {
                directInteractor.selectEntered.AddListener(OnGrabObject);
                directInteractor.selectExited.AddListener(OnReleaseObject);
            }
        }

        /// <summary>
        /// Update hand tracking data
        /// </summary>
        private void UpdateHandTracking()
        {
            if (!enableHandTracking) return;

            // Check if hand tracking is available
            bool wasActive = isHandTrackingActive;
            isHandTrackingActive = InputDevices.GetDeviceAtXRNode(handSide).TryGetFeatureValue(
                CommonUsages.isTracked, out bool tracked) && tracked;

            // Handle tracking state changes
            if (isHandTrackingActive != wasActive)
            {
                if (isHandTrackingActive)
                {
                    OnHandTrackingStarted();
                }
                else
                {
                    OnHandTrackingLost();
                }
            }

            // Update hand position and rotation
            if (isHandTrackingActive)
            {
                UpdateHandPose();
            }
        }

        /// <summary>
        /// Update finger tracking data
        /// </summary>
        private void UpdateFingerTracking()
        {
            if (!isHandTrackingActive) return;

            // Get finger tracking data from XR Input System
            InputDevice device = InputDevices.GetDeviceAtXRNode(handSide);

            // Update each finger
            UpdateFinger(device, FingerType.Thumb);
            UpdateFinger(device, FingerType.Index);
            UpdateFinger(device, FingerType.Middle);
            UpdateFinger(device, FingerType.Ring);
            UpdateFinger(device, FingerType.Pinky);

            // Update hand model if available
            UpdateHandModel();
        }

        /// <summary>
        /// Update individual finger tracking
        /// </summary>
        private void UpdateFinger(InputDevice device, FingerType fingerType)
        {
            var finger = fingerData[fingerType];

            // Try to get finger tracking data
            bool isTracked = device.TryGetFeatureValue(GetFingerUsage(fingerType), out Vector3 tipPos);

            if (isTracked)
            {
                finger.tipPosition = tipPos;
                finger.isTracking = true;

                // Calculate finger curl based on position relative to hand
                Vector3 localTipPos = transform.InverseTransformPoint(tipPos);
                finger.curl = Mathf.Clamp01(1f - localTipPos.z / 0.1f);
            }
            else
            {
                finger.isTracking = false;
                // Gradually return to neutral position
                finger.curl = Mathf.Lerp(finger.curl, 0f, Time.deltaTime * 5f);
            }

            fingerData[fingerType] = finger;
        }

        /// <summary>
        /// Get input usage for specific finger
        /// </summary>
        private InputFeatureUsage<Vector3> GetFingerUsage(FingerType fingerType)
        {
            switch (fingerType)
            {
                case FingerType.Thumb:
                    return CommonUsages.deviceRotation; // Fallback
                case FingerType.Index:
                    return CommonUsages.devicePosition; // Fallback
                case FingerType.Middle:
                    return CommonUsages.devicePosition; // Fallback
                case FingerType.Ring:
                    return CommonUsages.devicePosition; // Fallback
                case FingerType.Pinky:
                    return CommonUsages.devicePosition; // Fallback
                default:
                    return CommonUsages.devicePosition;
            }
        }

        /// <summary>
        /// Update hand pose and calculate velocities
        /// </summary>
        private void UpdateHandPose()
        {
            InputDevice device = InputDevices.GetDeviceAtXRNode(handSide);

            // Get position and rotation
            if (device.TryGetFeatureValue(CommonUsages.devicePosition, out Vector3 position) &&
                device.TryGetFeatureValue(CommonUsages.deviceRotation, out Quaternion rotation))
            {
                // Calculate velocities
                Vector3 velocity = (position - lastHandPosition) / Time.deltaTime;
                Quaternion angularVelocity = rotation * Quaternion.Inverse(lastHandRotation);

                lastHandPosition = position;
                lastHandRotation = rotation;

                // Trigger hand tracked event
                OnHandTracked?.Invoke(position);

                // Update transform
                transform.position = position;
                transform.rotation = rotation;

                // Detect hand motion for gestures like dice rolling
                DetectHandMotion(velocity);
            }
        }

        /// <summary>
        /// Update hand model with current tracking data
        /// </summary>
        private void UpdateHandModel()
        {
            if (handRenderer == null || handModelParent == null) return;

            // Update blend shapes based on finger curl values
            if (handRenderer.sharedMesh != null)
            {
                for (int i = 0; i < 5; i++)
                {
                    FingerType fingerType = (FingerType)i;
                    float curlValue = fingerData[fingerType].curl;

                    // Set blend shape weight (assuming blend shape naming convention)
                    string blendShapeName = $"Finger_{fingerType}_Curl";
                    int blendShapeIndex = handRenderer.sharedMesh.GetBlendShapeIndex(blendShapeName);

                    if (blendShapeIndex >= 0)
                    {
                        handRenderer.SetBlendShapeWeight(blendShapeIndex, curlValue * 100f);
                    }
                }
            }
        }

        /// <summary>
        /// Process gesture recognition
        /// </summary>
        private void ProcessGestures()
        {
            if (!isHandTrackingActive) return;

            foreach (var gesture in customGestures)
            {
                float confidence = CalculateGestureConfidence(gesture);
                currentGestureValues[gesture.gestureName] = confidence;

                // Check if gesture is detected
                if (confidence >= gestureConfidenceThreshold)
                {
                    // Check minimum hold time
                    if (Time.time - GetGestureStartTime(gesture.gestureName) >= gesture.minHoldTime)
                    {
                        OnGestureDetected?.Invoke(gesture.gestureName, transform.position, transform.rotation);
                        TriggerHapticFeedback(gesture.type);
                        ResetGestureStartTime(gesture.gestureName);
                    }
                }
                else
                {
                    ResetGestureStartTime(gesture.gestureName);
                }
            }
        }

        /// <summary>
        /// Calculate confidence score for a gesture
        /// </summary>
        private float CalculateGestureConfidence(GestureDefinition gesture)
        {
            float fingerConfidence = 0f;
            float orientationConfidence = 1f;

            // Compare finger patterns
            for (int i = 0; i < 5 && i < gesture.fingerCurlPattern.Length; i++)
            {
                FingerType fingerType = (FingerType)i;
                float actualCurl = fingerData[fingerType].curl;
                float expectedCurl = gesture.fingerCurlPattern[i];

                fingerConfidence += 1f - Mathf.Abs(actualCurl - expectedCurl);
            }

            fingerConfidence /= 5f; // Average across all fingers

            // Check hand orientation if required
            if (gesture.requireSteadyHand)
            {
                Vector3 currentOrientation = transform.forward;
                orientationConfidence = Vector3.Dot(currentOrientation.normalized, gesture.handOrientation.normalized);
            }

            // Check hand steadiness
            float stabilityConfidence = 1f;
            if (gesture.requireSteadyHand)
            {
                Vector3 velocity = (transform.position - lastHandPosition) / Time.deltaTime;
                stabilityConfidence = Mathf.Clamp01(1f - (velocity.magnitude / gesture.steadyHandThreshold));
            }

            return (fingerConfidence + orientationConfidence + stabilityConfidence) / 3f;
        }

        /// <summary>
        /// Detect hand motion for specific gestures
        /// </summary>
        private void DetectHandMotion(Vector3 velocity)
        {
            // Detect dice rolling motion (quick flick with rotation)
            if (velocity.magnitude > 2f && currentGestureValues.ContainsKey("DiceRoll"))
            {
                // Check for rotational component
                if (currentGestureValues["DiceRoll"] > 0.7f)
                {
                    // Trigger dice roll
                    OnGestureDetected?.Invoke("DiceRoll", transform.position, transform.rotation);
                    TriggerHapticFeedback(GestureType.DiceRoll);
                }
            }
        }

        /// <summary>
        /// Update interaction feedback
        /// </summary>
        private void UpdateInteractionFeedback()
        {
            // Update haptic feedback based on interaction
            if (grabbedObject != null)
            {
                // Provide continuous haptic feedback when holding objects
                if (enableHaptics && Time.time % 0.1f < Time.deltaTime)
                {
                    TriggerHapticFeedback(0.2f, 0.05f);
                }
            }
        }

        /// <summary>
        /// Trigger haptic feedback
        /// </summary>
        public void TriggerHapticFeedback(GestureType gestureType)
        {
            float amplitude = hapticAmplitude;
            float duration = hapticDuration;

            // Adjust feedback based on gesture type
            switch (gestureType)
            {
                case GestureType.DiceRoll:
                    amplitude = 0.8f;
                    duration = 0.3f;
                    break;
                case GestureType.SpellCast:
                    amplitude = 0.6f;
                    duration = 0.5f;
                    break;
                case GestureType.MiniatureSelect:
                    amplitude = 0.4f;
                    duration = 0.1f;
                    break;
            }

            TriggerHapticFeedback(amplitude, duration);
        }

        /// <summary>
        /// Trigger haptic feedback with custom parameters
        /// </summary>
        public void TriggerHapticFeedback(float amplitude, float duration)
        {
            if (!enableHaptics) return;

            OnHapticTrigger?.Invoke(amplitude);

            // Send haptic impulse to controller
            InputDevice device = InputDevices.GetDeviceAtXRNode(handSide);
            if (device.isValid)
            {
                uint channel = 0; // Default channel
                device.SendHapticImpulse(channel, amplitude, duration);
            }
        }

        /// <summary>
        /// Handle object grabbing
        /// </summary>
        private void OnGrabObject(SelectEnterEventArgs args)
        {
            grabbedObject = args.interactableObject as XRGrabInteractable;
            OnObjectGrabbed?.Invoke(grabbedObject.gameObject);

            // Trigger haptic feedback
            TriggerHapticFeedback(0.6f, 0.1f);
        }

        /// <summary>
        /// Handle object releasing
        /// </summary>
        private void OnReleaseObject(SelectExitEventArgs args)
        {
            OnObjectReleased?.Invoke(grabbedObject.gameObject);
            grabbedObject = null;

            // Trigger haptic feedback
            TriggerHapticFeedback(0.3f, 0.05f);
        }

        /// <summary>
        /// Handle hand tracking started
        /// </summary>
        private void OnHandTrackingStarted()
        {
            Debug.Log($"Hand tracking started for {handSide}");

            // Show hand model if available
            if (handModelParent != null)
            {
                handModelParent.gameObject.SetActive(true);
            }
        }

        /// <summary>
        /// Handle hand tracking lost
        /// </summary>
        private void OnHandTrackingLost()
        {
            Debug.Log($"Hand tracking lost for {handSide}");

            // Hide hand model
            if (handModelParent != null)
            {
                handModelParent.gameObject.SetActive(false);
            }

            // Reset finger tracking
            foreach (var finger in fingerData.Values)
            {
                finger.isTracking = false;
                finger.curl = 0f;
                finger.splay = 0f;
            }
        }

        /// <summary>
        /// Get gesture start time
        /// </summary>
        private float GetGestureStartTime(string gestureName)
        {
            // This would be stored in a dictionary with timestamps
            // For now, return current time
            return Time.time;
        }

        /// <summary>
        /// Reset gesture start time
        /// </summary>
        private void ResetGestureStartTime(string gestureName)
        {
            // Reset the gesture detection timer
            // Implementation depends on specific timing system
        }

        /// <summary>
        /// Check if specific gesture is currently detected
        /// </summary>
        public bool IsGestureDetected(string gestureName)
        {
            return currentGestureValues.ContainsKey(gestureName) &&
                   currentGestureValues[gestureName] >= gestureConfidenceThreshold;
        }

        /// <summary>
        /// Get current confidence value for a gesture
        /// </summary>
        public float GetGestureConfidence(string gestureName)
        {
            return currentGestureValues.ContainsKey(gestureName) ?
                   currentGestureValues[gestureName] : 0f;
        }

        /// <summary>
        /// Add custom gesture
        /// </summary>
        public void AddCustomGesture(GestureDefinition gesture)
        {
            customGestures.Add(gesture);
            currentGestureValues[gesture.gestureName] = 0f;
        }

        /// <summary>
        /// Get current finger tracking data
        /// </summary>
        public FingerTrackingData GetFingerData(FingerType fingerType)
        {
            return fingerData.ContainsKey(fingerType) ? fingerData[fingerType] : new FingerTrackingData();
        }

        private void OnDestroy()
        {
            // Cleanup event listeners
            if (directInteractor != null)
            {
                directInteractor.selectEntered.RemoveListener(OnGrabObject);
                directInteractor.selectExited.RemoveListener(OnReleaseObject);
            }
        }

        private void OnDrawGizmos()
        {
            if (!showDebugVisualization) return;

            // Draw hand position
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(transform.position, 0.05f);

            // Draw finger positions if tracking
            if (isHandTrackingActive)
            {
                foreach (var finger in fingerData.Values)
                {
                    if (finger.isTracking)
                    {
                        Gizmos.color = Color.yellow;
                        Gizmos.DrawWireSphere(finger.tipPosition, 0.02f);
                    }
                }
            }
        }
    }

    /// <summary>
    /// Hand tracking data source for XR input
    /// </summary>
    public class HandTrackingDataSource
    {
        private XRNode handNode;
        private InputDevice device;

        public HandTrackingDataSource(XRNode node)
        {
            handNode = node;
            device = InputDevices.GetDeviceAtXRNode(node);
        }

        public bool IsTracking()
        {
            return device.isValid && device.TryGetFeatureValue(CommonUsages.isTracked, out bool tracked) && tracked;
        }

        public Vector3 GetPosition()
        {
            if (device.TryGetFeatureValue(CommonUsages.devicePosition, out Vector3 position))
                return position;
            return Vector3.zero;
        }

        public Quaternion GetRotation()
        {
            if (device.TryGetFeatureValue(CommonUsages.deviceRotation, out Quaternion rotation))
                return rotation;
            return Quaternion.identity;
        }
    }
}