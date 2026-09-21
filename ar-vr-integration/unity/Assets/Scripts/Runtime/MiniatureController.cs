using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using System.Collections;

namespace DND.ARVR
{
    /// <summary>
    /// Controller for D&D miniatures in VR/AR
    /// Handles interactions, animations, and state management
    /// </summary>
    public class MiniatureController : MonoBehaviour
    {
        [Header("Miniature Settings")]
        [SerializeField] private string miniatureName = "Character";
        [SerializeField] private int health = 100;
        [SerializeField] private int maxHealth = 100;
        [SerializeField] private int armorClass = 14;
        [SerializeField] private int movementSpeed = 30;
        [SerializeField] private bool isPlayer = false;
        [SerializeField] private bool isEnemy = false;

        [Header("Visual Settings")]
        [SerializeField] private Material highlightMaterial;
        [SerializeField] private Material damagedMaterial;
        [SerializeField] private float highlightDuration = 2f;
        [SerializeField] private float damagedDuration = 1f;

        [Header("Animation Settings")]
        [SerializeField] private bool enableAnimations = true;
        [SerializeField] private float rotationSpeed = 90f;
        [SerializeField] private float moveSpeed = 5f;

        // Components
        private Rigidbody rb;
        private XRGrabInteractable grabInteractable;
        private Renderer[] renderers;
        private Material[] originalMaterials;
        private Animator animator;

        // State
        private bool isSelected = false;
        private bool isHovered = false;
        private bool isDamaged = false;
        private Vector3 targetPosition;
        private Quaternion targetRotation;
        private bool isMoving = false;
        private bool isRotating = false;

        // Events
        public System.Action<MiniatureController> OnSelected;
        public System.Action<MiniatureController> OnDeselected;
        public System.Action<MiniatureController, int> OnHealthChanged;
        public System.Action<MiniatureController> OnDeath;
        public System.Action<MiniatureController> OnMoved;

        private DNDTabletopManager tabletopManager;

        private void Awake()
        {
            InitializeComponents();
        }

        private void Start()
        {
            SetupInteractions();
        }

        private void Update()
        {
            HandleMovement();
            HandleRotation();
            HandleHoverEffects();
        }

        private void InitializeComponents()
        {
            rb = GetComponent<Rigidbody>();
            grabInteractable = GetComponent<XRGrabInteractable>();
            renderers = GetComponentsInChildren<Renderer>();

            // Store original materials
            originalMaterials = new Material[renderers.Length];
            for (int i = 0; i < renderers.Length; i++)
            {
                originalMaterials[i] = renderers[i].material;
            }

            // Get animator
            animator = GetComponent<Animator>();
        }

        private void SetupInteractions()
        {
            if (grabInteractable != null)
            {
                grabInteractable.activated.AddListener(OnGrabbed);
                grabInteractable.deactivated.AddListener(OnReleased);
                grabInteractable.hoverEntered.AddListener(OnHoverEntered);
                grabInteractable.hoverExited.AddListener(OnHoverExited);
            }
        }

        public void Initialize(DNDTabletopManager manager)
        {
            tabletopManager = manager;
        }

        public void OnGrabbed(ActivateEventArgs args)
        {
            // Handle grab/selection
            SelectMiniature();
        }

        public void OnReleased(DeactivateEventArgs args)
        {
            // Handle release
            // Check if miniature should snap to grid
            SnapToGrid();
        }

        public void OnHoverEntered(HoverEnterEventArgs args)
        {
            isHovered = true;
            if (!isSelected)
            {
                HighlightMiniature();
            }
        }

        public void OnHoverExited(HoverExitEventArgs args)
        {
            isHovered = false;
            if (!isSelected)
            {
                RestoreOriginalMaterial();
            }
        }

        public void SelectMiniature()
        {
            if (isSelected) return;

            isSelected = true;
            HighlightMiniature();

            // Disable physics while selected
            if (rb != null)
            {
                rb.isKinematic = true;
            }

            OnSelected?.Invoke(this);
        }

        public void DeselectMiniature()
        {
            if (!isSelected) return;

            isSelected = false;
            RestoreOriginalMaterial();

            // Re-enable physics
            if (rb != null)
            {
                rb.isKinematic = false;
            }

            OnDeselected?.Invoke(this);
        }

        private void HighlightMiniature()
        {
            if (highlightMaterial == null) return;

            foreach (var renderer in renderers)
            {
                if (renderer != null)
                {
                    renderer.material = highlightMaterial;
                }
            }
        }

        private void RestoreOriginalMaterial()
        {
            if (isDamaged) return;

            for (int i = 0; i < renderers.Length; i++)
            {
                if (renderers[i] != null && originalMaterials[i] != null)
                {
                    renderers[i].material = originalMaterials[i];
                }
            }
        }

        public void TakeDamage(int damage)
        {
            health = Mathf.Max(0, health - damage);

            // Show damage effect
            StartCoroutine(ShowDamageEffect());

            // Play damage animation
            if (animator != null && enableAnimations)
            {
                animator.SetTrigger("TakeDamage");
            }

            // Check for death
            if (health <= 0)
            {
                Die();
            }

            OnHealthChanged?.Invoke(this, health);
        }

        public void Heal(int amount)
        {
            health = Mathf.Min(maxHealth, health + amount);
            OnHealthChanged?.Invoke(this, health);
        }

        private IEnumerator ShowDamageEffect()
        {
            isDamaged = true;

            // Apply damaged material
            if (damagedMaterial != null)
            {
                foreach (var renderer in renderers)
                {
                    if (renderer != null)
                    {
                        renderer.material = damagedMaterial;
                    }
                }
            }

            // Flash red
            for (int i = 0; i < 3; i++)
            {
                // Flash on
                foreach (var renderer in renderers)
                {
                    if (renderer != null)
                    {
                        renderer.material.color = Color.red;
                    }
                }
                yield return new WaitForSeconds(0.1f);

                // Flash off
                RestoreOriginalMaterial();
                yield return new WaitForSeconds(0.1f);
            }

            isDamaged = false;
        }

        private void Die()
        {
            // Play death animation
            if (animator != null && enableAnimations)
            {
                animator.SetTrigger("Death");
            }

            // Disable interactions
            if (grabInteractable != null)
            {
                grabInteractable.enabled = false;
            }

            // Make miniature fall over
            if (rb != null)
            {
                rb.isKinematic = false;
                rb.AddTorque(transform.right * 5f, ForceMode.Impulse);
            }

            // Start coroutine to destroy after animation
            StartCoroutine(DestroyAfterDelay(5f));

            OnDeath?.Invoke(this);
        }

        private IEnumerator DestroyAfterDelay(float delay)
        {
            yield return new WaitForSeconds(delay);
            Destroy(gameObject);
        }

        public void MoveTo(Vector3 position, bool snap = false)
        {
            if (snap)
            {
                transform.position = position;
                OnMoved?.Invoke(this);
            }
            else
            {
                targetPosition = position;
                isMoving = true;

                if (animator != null && enableAnimations)
                {
                    animator.SetBool("IsMoving", true);
                }
            }
        }

        public void RotateTo(Quaternion rotation, bool snap = false)
        {
            if (snap)
            {
                transform.rotation = rotation;
            }
            else
            {
                targetRotation = rotation;
                isRotating = true;
            }
        }

        private void HandleMovement()
        {
            if (!isMoving) return;

            float step = moveSpeed * Time.deltaTime;
            transform.position = Vector3.MoveTowards(transform.position, targetPosition, step);

            if (Vector3.Distance(transform.position, targetPosition) < 0.01f)
            {
                isMoving = false;

                if (animator != null && enableAnimations)
                {
                    animator.SetBool("IsMoving", false);
                }

                OnMoved?.Invoke(this);
            }
        }

        private void HandleRotation()
        {
            if (!isRotating) return;

            float step = rotationSpeed * Time.deltaTime;
            transform.rotation = Quaternion.RotateTowards(transform.rotation, targetRotation, step);

            if (Quaternion.Angle(transform.rotation, targetRotation) < 1f)
            {
                isRotating = false;
            }
        }

        private void HandleHoverEffects()
        {
            if (isHovered && !isSelected)
            {
                // Gentle floating effect
                float hoverOffset = Mathf.Sin(Time.time * 2f) * 0.05f;
                transform.position = new Vector3(
                    transform.position.x,
                    transform.position.y + hoverOffset,
                    transform.position.z
                );
            }
        }

        private void SnapToGrid()
        {
            // Snap to a grid (assuming 1 unit grid)
            Vector3 snappedPosition = new Vector3(
                Mathf.Round(transform.position.x),
                transform.position.y,
                Mathf.Round(transform.position.z)
            );

            transform.position = snappedPosition;
        }

        // Public getters and setters
        public string MiniatureName
        {
            get => miniatureName;
            set => miniatureName = value;
        }

        public int Health
        {
            get => health;
            set => health = Mathf.Clamp(value, 0, maxHealth);
        }

        public int MaxHealth
        {
            get => maxHealth;
            set => maxHealth = Mathf.Max(1, value);
        }

        public int ArmorClass
        {
            get => armorClass;
            set => armorClass = Mathf.Max(0, value);
        }

        public int MovementSpeed
        {
            get => movementSpeed;
            set => movementSpeed = Mathf.Max(0, value);
        }

        public bool IsPlayer
        {
            get => isPlayer;
            set => isPlayer = value;
        }

        public bool IsEnemy
        {
            get => isEnemy;
            set => isEnemy = value;
        }

        public bool IsSelected
        {
            get => isSelected;
        }

        public bool IsHovered
        {
            get => isHovered;
        }

        public bool IsMoving
        {
            get => isMoving;
        }

        public bool IsDead
        {
            get => health <= 0;
        }

        // Utility methods
        public void SetHealth(int currentHealth, int maxHp = -1)
        {
            if (maxHp > 0)
            {
                maxHealth = maxHp;
            }
            health = Mathf.Clamp(currentHealth, 0, maxHealth);
            OnHealthChanged?.Invoke(this, health);
        }

        public void FullHeal()
        {
            health = maxHealth;
            OnHealthChanged?.Invoke(this, health);
        }

        public void SetHighlight(Material material)
        {
            highlightMaterial = material;
        }

        public void SetDamagedMaterial(Material material)
        {
            damagedMaterial = material;
        }

        private void OnDestroy()
        {
            // Cleanup event listeners
            if (grabInteractable != null)
            {
                grabInteractable.activated.RemoveListener(OnGrabbed);
                grabInteractable.deactivated.RemoveListener(OnReleased);
                grabInteractable.hoverEntered.RemoveListener(OnHoverEntered);
                grabInteractable.hoverExited.RemoveListener(OnHoverExited);
            }
        }

        private void OnDrawGizmosSelected()
        {
            // Draw health bar
            if (health > 0)
            {
                Gizmos.color = Color.green;
                Vector3 healthBarPos = transform.position + Vector3.up * 1.5f;
                Vector3 healthBarSize = new Vector3(1f * (float)health / maxHealth, 0.1f, 0.1f);
                Gizmos.DrawCube(healthBarPos, healthBarSize);

                Gizmos.color = Color.red;
                Vector3 missingHealthSize = new Vector3(1f * (1f - (float)health / maxHealth), 0.1f, 0.1f);
                Gizmos.DrawCube(healthBarPos + Vector3.right * ((float)health / maxHealth - 0.5f), missingHealthSize);
            }

            // Draw movement radius
            Gizmos.color = Color.blue;
            Gizmos.DrawWireSphere(transform.position, movementSpeed * 0.1f); // Scale down for visualization
        }
    }
}