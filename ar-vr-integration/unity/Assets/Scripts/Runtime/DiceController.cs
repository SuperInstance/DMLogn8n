using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using System.Collections;
using System.Collections.Generic;

namespace DND.ARVR
{
    /// <summary>
    /// Controller for D&D dice in VR/AR
    /// Handles physics, rolling, and result calculation
    /// </summary>
    public class DiceController : MonoBehaviour
    {
        [Header("Dice Settings")]
        [SerializeField] private int diceSides = 6;
        [SerializeField] private float rollDuration = 3f;
        [SerializeField] private float minRollVelocity = 0.1f;
        [SerializeField] private LayerMask tableLayer;

        [Header("Visual Settings")]
        [SerializeField] private Material[] faceMaterials;
        [SerializeField] private Color[] faceColors;
        [SerializeField] private float resultDisplayDuration = 5f;
        [SerializeField] private GameObject resultPrefab;

        [Header("Audio Settings")]
        [SerializeField] private AudioClip rollSound;
        [SerializeField] private AudioClip impactSound;
        [SerializeField] private AudioClip resultSound;
        [SerializeField] private float audioVolume = 0.5f;

        // Components
        private Rigidbody rb;
        private XRGrabInteractable grabInteractable;
        private AudioSource audioSource;
        private MeshFilter meshFilter;
        private DiceFace[] diceFaces;

        // State
        private bool isRolling = false;
        private bool hasLanded = false;
        private int currentResult = 1;
        private float rollStartTime;
        private Vector3 lastPosition;
        private Quaternion lastRotation;
        private Vector3 velocity;
        private Vector3 angularVelocity;
        private float settleTime;
        private bool hasSettled = false;

        // Events
        public System.Action<DiceController, int> OnRollStarted;
        public System.Action<DiceController, int> OnRollComplete;
        public System.Action<DiceController> OnDiceSettled;

        private DNDTabletopManager tabletopManager;

        private void Awake()
        {
            InitializeComponents();
        }

        private void Start()
        {
            SetupDiceFaces();
            SetupInteractions();
        }

        private void Update()
        {
            if (isRolling && !hasSettled)
            {
                CheckIfSettled();
            }
        }

        private void FixedUpdate()
        {
            if (isRolling)
            {
                TrackVelocity();
            }
        }

        private void InitializeComponents()
        {
            rb = GetComponent<Rigidbody>();
            grabInteractable = GetComponent<XRGrabInteractable>();
            audioSource = GetComponent<AudioSource>();
            meshFilter = GetComponent<MeshFilter>();

            if (audioSource == null)
            {
                audioSource = gameObject.AddComponent<AudioSource>();
                audioSource.spatialBlend = 1f; // 3D sound
                audioSource.volume = audioVolume;
            }

            lastPosition = transform.position;
            lastRotation = transform.rotation;
        }

        private void SetupDiceFaces()
        {
            // Create dice face detection based on dice type
            diceFaces = CreateDiceFaces(diceSides);
        }

        private DiceFace[] CreateDiceFaces(int sides)
        {
            return sides switch
            {
                4 => CreateD4Faces(),
                6 => CreateD6Faces(),
                8 => CreateD8Faces(),
                10 => CreateD10Faces(),
                12 => CreateD12Faces(),
                20 => CreateD20Faces(),
                _ => CreateD6Faces() // Default to d6
            };
        }

        private DiceFace[] CreateD4Faces()
        {
            return new DiceFace[]
            {
                new DiceFace(1, Vector3.up, Quaternion.Euler(0f, 0f, 0f)),
                new DiceFace(2, Vector3.right, Quaternion.Euler(0f, 90f, 0f)),
                new DiceFace(3, Vector3.forward, Quaternion.Euler(90f, 0f, 0f)),
                new DiceFace(4, Vector3.left, Quaternion.Euler(0f, -90f, 0f))
            };
        }

        private DiceFace[] CreateD6Faces()
        {
            return new DiceFace[]
            {
                new DiceFace(1, Vector3.up, Quaternion.Euler(0f, 0f, 0f)),
                new DiceFace(2, Vector3.down, Quaternion.Euler(180f, 0f, 0f)),
                new DiceFace(3, Vector3.forward, Quaternion.Euler(90f, 0f, 0f)),
                new DiceFace(4, Vector3.back, Quaternion.Euler(-90f, 0f, 0f)),
                new DiceFace(5, Vector3.right, Quaternion.Euler(0f, -90f, 0f)),
                new DiceFace(6, Vector3.left, Quaternion.Euler(0f, 90f, 0f))
            };
        }

        private DiceFace[] CreateD8Faces()
        {
            // D8 has 8 triangular faces
            var faces = new DiceFace[8];
            for (int i = 0; i < 8; i++)
            {
                float angle = i * 45f;
                Vector3 normal = Quaternion.Euler(angle, 0f, 45f) * Vector3.up;
                faces[i] = new DiceFace(i + 1, normal, Quaternion.LookRotation(normal));
            }
            return faces;
        }

        private DiceFace[] CreateD10Faces()
        {
            // D10 is a pentagonal trapezohedron
            var faces = new DiceFace[10];
            for (int i = 0; i < 10; i++)
            {
                float angle = i * 36f;
                Vector3 normal = Quaternion.Euler(angle, 0f, 0f) * Vector3.up;
                faces[i] = new DiceFace((i % 10) + 1, normal, Quaternion.LookRotation(normal));
            }
            return faces;
        }

        private DiceFace[] CreateD12Faces()
        {
            // D12 has 12 pentagonal faces
            var faces = new DiceFace[12];
            for (int i = 0; i < 12; i++)
            {
                float angle = i * 30f;
                Vector3 normal = Quaternion.Euler(angle, 0f, 0f) * Vector3.up;
                faces[i] = new DiceFace(i + 1, normal, Quaternion.LookRotation(normal));
            }
            return faces;
        }

        private DiceFace[] CreateD20Faces()
        {
            // D20 has 20 triangular faces (icosahedron)
            var faces = new DiceFace[20];
            for (int i = 0; i < 20; i++)
            {
                float angle = i * 18f;
                Vector3 normal = Quaternion.Euler(angle, 0f, 0f) * Vector3.up;
                faces[i] = new DiceFace(i + 1, normal, Quaternion.LookRotation(normal));
            }
            return faces;
        }

        private void SetupInteractions()
        {
            if (grabInteractable != null)
            {
                grabInteractable.activated.AddListener(OnGrabbed);
                grabInteractable.deactivated.AddListener(OnReleased);
            }
        }

        public void Initialize(DNDTabletopManager manager, int sides)
        {
            tabletopManager = manager;
            diceSides = sides;
            SetupDiceFaces();
        }

        public void OnGrabbed(ActivateEventArgs args)
        {
            // Reset dice state when grabbed
            isRolling = false;
            hasLanded = false;
            hasSettled = false;
            currentResult = 1;

            // Enable physics
            if (rb != null)
            {
                rb.isKinematic = false;
            }
        }

        public void OnReleased(DeactivateEventArgs args)
        {
            // Start rolling when released
            StartRoll();
        }

        public void StartRoll()
        {
            if (isRolling) return;

            isRolling = true;
            hasLanded = false;
            hasSettled = false;
            rollStartTime = Time.time;

            // Add random force for rolling
            if (rb != null)
            {
                Vector3 randomForce = new Vector3(
                    Random.Range(-5f, 5f),
                    Random.Range(2f, 5f),
                    Random.Range(-5f, 5f)
                );
                rb.AddForce(randomForce, ForceMode.Impulse);

                Vector3 randomTorque = new Vector3(
                    Random.Range(-10f, 10f),
                    Random.Range(-10f, 10f),
                    Random.Range(-10f, 10f)
                );
                rb.AddTorque(randomTorque, ForceMode.Impulse);
            }

            // Play roll sound
            PlaySound(rollSound);

            OnRollStarted?.Invoke(this, currentResult);
        }

        private void TrackVelocity()
        {
            if (rb == null) return;

            velocity = (transform.position - lastPosition) / Time.fixedDeltaTime;
            angularVelocity = (transform.rotation.eulerAngles - lastRotation.eulerAngles) / Time.fixedDeltaTime;

            lastPosition = transform.position;
            lastRotation = transform.rotation;
        }

        private void CheckIfSettled()
        {
            if (rb == null) return;

            // Check if dice has stopped moving
            if (velocity.magnitude < minRollVelocity && angularVelocity.magnitude < minRollVelocity)
            {
                if (!hasLanded)
                {
                    hasLanded = true;
                    settleTime = Time.time;
                    PlaySound(impactSound);
                }

                // Check if dice has been settled for enough time
                if (Time.time - settleTime > 0.5f)
                {
                    SettleDice();
                }
            }
            else
            {
                hasLanded = false;
            }
        }

        private void SettleDice()
        {
            if (hasSettled) return;

            hasSettled = true;
            isRolling = false;

            // Make dice kinematic to prevent further movement
            if (rb != null)
            {
                rb.velocity = Vector3.zero;
                rb.angularVelocity = Vector3.zero;
                rb.isKinematic = true;
            }

            // Calculate which face is up
            currentResult = CalculateUpwardFace();

            // Display result
            DisplayResult();

            // Play result sound
            PlaySound(resultSound);

            OnRollComplete?.Invoke(this, currentResult);
            OnDiceSettled?.Invoke(this);

            // Start auto-destroy coroutine
            StartCoroutine(AutoDestroyAfterDelay());
        }

        private int CalculateUpwardFace()
        {
            if (diceFaces == null || diceFaces.Length == 0)
            {
                return 1;
            }

            int highestFace = 1;
            float highestDot = -1f;

            foreach (var face in diceFaces)
            {
                float dotProduct = Vector3.Dot(face.Normal, Vector3.up);
                if (dotProduct > highestDot)
                {
                    highestDot = dotProduct;
                    highestFace = face.Value;
                }
            }

            return highestFace;
        }

        private void DisplayResult()
        {
            if (resultPrefab == null) return;

            // Create result display
            Vector3 resultPosition = transform.position + Vector3.up * 0.5f;
            GameObject resultDisplay = Instantiate(resultPrefab, resultPosition, Quaternion.identity);

            // Set result text
            var resultText = resultDisplay.GetComponentInChildren<TextMesh>();
            if (resultText != null)
            {
                resultText.text = currentResult.ToString();
                resultText.fontSize = 100;
                resultText.color = GetResultColor();
            }

            // Make result face camera
            resultDisplay.transform.LookAt(Camera.main.transform);

            // Start fade animation
            StartCoroutine(FadeResultDisplay(resultDisplay));

            // Apply color to upward face
            ColorUpwardFace();
        }

        private Color GetResultColor()
        {
            return currentResult switch
            {
                var n when n == diceSides => Color.green, // Critical success
                var n when n == 1 => Color.red,           // Critical failure
                var n when n >= diceSides * 0.8 => Color.yellow, // High roll
                var n when n <= diceSides * 0.2 => Color.orange, // Low roll
                _ => Color.white
            };
        }

        private void ColorUpwardFace()
        {
            if (diceFaces == null || faceColors == null || faceColors.Length == 0) return;

            // Find the upward face and apply color
            int upwardFaceIndex = currentResult - 1;
            if (upwardFaceIndex >= 0 && upwardFaceIndex < faceColors.Length)
            {
                Color resultColor = GetResultColor();
                // Apply color to dice material or create highlight effect
                var renderer = GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material.color = resultColor;
                }
            }
        }

        private IEnumerator FadeResultDisplay(GameObject resultDisplay)
        {
            float fadeDuration = 1f;
            float fadeStart = Time.time;

            var textMesh = resultDisplay.GetComponentInChildren<TextMesh>();
            var renderer = resultDisplay.GetComponent<Renderer>();

            while (Time.time - fadeStart < fadeDuration)
            {
                float progress = (Time.time - fadeStart) / fadeDuration;
                float alpha = 1f - progress;

                if (textMesh != null)
                {
                    Color color = textMesh.color;
                    color.a = alpha;
                    textMesh.color = color;
                }

                if (renderer != null)
                {
                    Color color = renderer.material.color;
                    color.a = alpha;
                    renderer.material.color = color;
                }

                yield return null;
            }

            Destroy(resultDisplay);
        }

        private IEnumerator AutoDestroyAfterDelay()
        {
            yield return new WaitForSeconds(resultDisplayDuration);

            // Optional: Fade out and destroy dice
            StartCoroutine(FadeAndDestroy());
        }

        private IEnumerator FadeAndDestroy()
        {
            float fadeDuration = 1f;
            float fadeStart = Time.time;
            var renderer = GetComponent<Renderer>();

            while (Time.time - fadeStart < fadeDuration)
            {
                float progress = (Time.time - fadeStart) / fadeDuration;
                float alpha = 1f - progress;

                if (renderer != null)
                {
                    Color color = renderer.material.color;
                    color.a = alpha;
                    renderer.material.color = color;
                }

                yield return null;
            }

            Destroy(gameObject);
        }

        private void PlaySound(AudioClip clip)
        {
            if (audioSource != null && clip != null)
            {
                audioSource.PlayOneShot(clip);
            }
        }

        private void OnCollisionEnter(Collision collision)
        {
            if (isRolling && !hasSettled)
            {
                // Play impact sound
                PlaySound(impactSound);

                // Check if landed on table
                if (((1 << collision.gameObject.layer) & tableLayer) != 0)
                {
                    hasLanded = true;
                    settleTime = Time.time;
                }
            }
        }

        // Public API methods
        public void ForceResult(int result)
        {
            currentResult = Mathf.Clamp(result, 1, diceSides);
            SettleDice();
        }

        public void ResetDice()
        {
            isRolling = false;
            hasLanded = false;
            hasSettled = false;
            currentResult = 1;

            if (rb != null)
            {
                rb.velocity = Vector3.zero;
                rb.angularVelocity = Vector3.zero;
                rb.isKinematic = false;
            }

            // Reset material color
            var renderer = GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = Color.white;
            }
        }

        // Getters
        public int DiceSides => diceSides;
        public int CurrentResult => currentResult;
        public bool IsRolling => isRolling;
        public bool HasSettled => hasSettled;
        public float RollDuration => Time.time - rollStartTime;

        private void OnDestroy()
        {
            // Cleanup event listeners
            if (grabInteractable != null)
            {
                grabInteractable.activated.RemoveListener(OnGrabbed);
                grabInteractable.deactivated.RemoveListener(OnReleased);
            }
        }

        private void OnDrawGizmosSelected()
        {
            // Draw dice faces normals for debugging
            if (diceFaces != null)
            {
                Gizmos.color = Color.blue;
                foreach (var face in diceFaces)
                {
                    Vector3 worldNormal = transform.TransformDirection(face.Normal);
                    Gizmos.DrawRay(transform.position, worldNormal * 0.5f);
                }
            }

            // Show current result
            if (hasSettled)
            {
                Gizmos.color = GetResultColor();
                Gizmos.DrawSphere(transform.position + Vector3.up * 1f, 0.2f);
            }
        }
    }

    /// <summary>
    /// Represents a face of a die with its value and orientation
    /// </summary>
    [System.Serializable]
    public class DiceFace
    {
        public int Value;
        public Vector3 Normal;
        public Quaternion Rotation;

        public DiceFace(int value, Vector3 normal, Quaternion rotation)
        {
            Value = value;
            Normal = normal.normalized;
            Rotation = rotation;
        }
    }
}