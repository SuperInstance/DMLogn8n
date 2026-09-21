using UnityEngine;
using UnityEngine.UI;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;
using System.Collections.Generic;
using System.Collections;
using System.Linq;
using TMPro;

namespace DMLog.VR
{
    /// <summary>
    /// Revolutionary VR Character Creator with 3D Avatar Customization
    /// Features real-time preview, extensive customization options, and animation library
    /// </summary>
    public class VRCharacterCreator : MonoBehaviour
    {
        [Header("Character Creator UI")]
        [SerializeField] private Canvas uiCanvas;
        [SerializeField] private GameObject customizationPanel;
        [SerializeField] private Button saveButton;
        [SerializeField] private Button randomizeButton;
        [SerializeField] private Button resetButton;
        [SerializeField] private TextMeshProUGUI characterNameText;

        [Header("Character Model")]
        [SerializeField] private GameObject characterBasePrefab;
        [SerializeField] private Transform characterPreviewTransform;
        [SerializeField] private SkinnedMeshRenderer characterRenderer;
        [SerializeField] private Animator characterAnimator;

        [Header("Customization Categories")]
        [SerializeField] private List<CustomizationCategory> categories = new List<CustomizationCategory>();
        [SerializeField] private GameObject categoryButtonPrefab;
        [SerializeField] private Transform categoryButtonParent;

        [Header("Appearance Options")]
        [SerializeField] private List<Material> skinMaterials = new List<Material>();
        [SerializeField] private List<Material> hairMaterials = new List<Material>();
        [SerializeField] private List<Material> eyeMaterials = new List<Material>();
        [SerializeField] private List<GameObject> hairStyles = new List<GameObject>();
        [SerializeField] private List<GameObject> facialHair = new List<GameObject>();
        [SerializeField] private List<GameObject> accessories = new List<GameObject>();

        [Header("Body Customization")]
        [SerializeField] private float minHeight = 1.5f;
        [SerializeField] private float maxHeight = 2.2f;
        [SerializeField] private float minMuscle = 0f;
        [SerializeField] private float maxMuscle = 1f;
        [SerializeField] private float minWeight = 0f;
        [SerializeField] private float maxWeight = 1f;

        [Header("Equipment System")]
        [SerializeField] private Transform equipmentParent;
        [SerializeField] private List<EquipmentSlot> equipmentSlots = new List<EquipmentSlot>();
        [SerializeField] private List<ArmorSet> armorSets = new List<ArmorSet>();
        [SerializeField] private List<Weapon> weapons = new List<Weapon>();

        [Header("Animation Preview")]
        [SerializeField] private List<AnimationClip> previewAnimations = new List<AnimationClip>();
        [SerializeField] private float animationPreviewDuration = 3f;
        [SerializeField] private bool autoRotatePreview = true;
        [SerializeField] private float rotationSpeed = 30f;

        // Private state
        private GameObject currentCharacter;
        private CharacterData currentCharacterData = new CharacterData();
        private CustomizationCategory activeCategory;
        private Dictionary<string, GameObject> currentEquipment = new Dictionary<string, GameObject>();
        private VRHandController leftHandController, rightHandController;
        private bool isCreatingCharacter = false;
        private Coroutine animationPreviewCoroutine;

        // Events
        public System.Action<CharacterData> OnCharacterCreated;
        public System.Action<CharacterData> OnCharacterUpdated;
        public System.Action<string> OnCategoryChanged;

        [System.Serializable]
        public class CustomizationCategory
        {
            public string categoryName;
            public string iconPath;
            public List<CustomizationOption> options = new List<CustomizationOption>();
            public bool isUnlocked = true;
        }

        [System.Serializable]
        public class CustomizationOption
        {
            public string optionName;
            public string displayName;
            public GameObject prefab;
            public Material material;
            public Texture2D thumbnail;
            public int cost = 0;
            public bool isUnlocked = true;
        }

        [System.Serializable]
        public class EquipmentSlot
        {
            public string slotName;
            public Transform slotTransform;
            public EquipmentType type;
            public GameObject currentEquipment;
        }

        public enum EquipmentType
        {
            Helmet, Chestplate, Gloves, Boots, Belt, Cloak, Weapon, Shield
        }

        [System.Serializable]
        public class ArmorSet
        {
            public string setName;
            public EquipmentType type;
            public GameObject armorPrefab;
            public Material armorMaterial;
            public List<string> compatibleRaces = new List<string>();
            public int defenseValue = 0;
            public int weight = 0;
        }

        [System.Serializable]
        public class Weapon
        {
            public string weaponName;
            public WeaponType type;
            public GameObject weaponPrefab;
            public int damage = 0;
            public float range = 1f;
            public List<string> compatibleClasses = new List<string>();
        }

        public enum WeaponType
        {
            Sword, Axe, Mace, Bow, Staff, Dagger, Spear, TwoHandedSword
        }

        [System.Serializable]
        public class CharacterData
        {
            public string characterName = "New Character";
            public string characterId;
            public CharacterRace race = CharacterRace.Human;
            public CharacterClass characterClass = CharacterClass.Fighter;
            public int level = 1;
            public Gender gender = Gender.Male;

            // Appearance
            public float height = 1.8f;
            public float muscle = 0.5f;
            public float weight = 0.5f;
            public int skinToneIndex = 0;
            public int hairStyleIndex = 0;
            public int hairColorIndex = 0;
            public int eyeColorIndex = 0;
            public int facialHairIndex = 0;

            // Equipment
            public Dictionary<string, string> equippedItems = new Dictionary<string, string>();

            // Animation
            public string idleAnimation = "Idle";
            public string walkAnimation = "Walk";
            public string runAnimation = "Run";
        }

        public enum CharacterRace
        {
            Human, Elf, Dwarf, Halfling, Dragonborn, Gnome, HalfElf, HalfOrc, Tiefling
        }

        public enum CharacterClass
        {
            Fighter, Wizard, Cleric, Rogue, Ranger, Paladin, Barbarian, Bard, Druid, Monk, Sorcerer, Warlock
        }

        public enum Gender
        {
            Male, Female, NonBinary
        }

        private void Awake()
        {
            InitializeCharacterCreator();
        }

        private void Start()
        {
            SetupUI();
            CreateCharacterPreview();
            SetupHandControllers();
            GenerateCharacterId();
        }

        private void Update()
        {
            HandleInput();
            UpdatePreviewRotation();
        }

        /// <summary>
        /// Initialize the VR character creator
        /// </summary>
        private void InitializeCharacterCreator()
        {
            Debug.Log("Initializing VR Character Creator");

            // Setup UI canvas for VR
            if (uiCanvas != null)
            {
                uiCanvas.renderMode = RenderMode.WorldSpace;
                uiCanvas.worldCamera = Camera.main;
            }

            // Initialize default categories if empty
            if (categories.Count == 0)
            {
                CreateDefaultCategories();
            }

            // Initialize equipment slots
            InitializeEquipmentSlots();

            Debug.Log("VR Character Creator initialized");
        }

        /// <summary>
        /// Setup user interface elements
        /// </summary>
        private void SetupUI()
        {
            // Create category buttons
            CreateCategoryButtons();

            // Setup button listeners
            if (saveButton != null)
            {
                saveButton.onClick.AddListener(SaveCharacter);
            }

            if (randomizeButton != null)
            {
                randomizeButton.onClick.AddListener(RandomizeCharacter);
            }

            if (resetButton != null)
            {
                resetButton.onClick.AddListener(ResetCharacter);
            }

            // Set initial category
            if (categories.Count > 0)
            {
                SetActiveCategory(categories[0]);
            }
        }

        /// <summary>
        /// Create default customization categories
        /// </summary>
        private void CreateDefaultCategories()
        {
            // Race category
            var raceCategory = new CustomizationCategory
            {
                categoryName = "Race",
                iconPath = "Icons/Race"
            };

            foreach (CharacterRace race in System.Enum.GetValues(typeof(CharacterRace)))
            {
                raceCategory.options.Add(new CustomizationOption
                {
                    optionName = race.ToString(),
                    displayName = race.ToString(),
                    isUnlocked = true
                });
            }
            categories.Add(raceCategory);

            // Appearance category
            var appearanceCategory = new CustomizationCategory
            {
                categoryName = "Appearance",
                iconPath = "Icons/Appearance"
            };

            // Add appearance options
            appearanceCategory.options.Add(new CustomizationOption
            {
                optionName = "Height",
                displayName = "Height"
            });

            appearanceCategory.options.Add(new CustomizationOption
            {
                optionName = "Muscle",
                displayName = "Muscle"
            });

            appearanceCategory.options.Add(new CustomizationOption
            {
                optionName = "Weight",
                displayName = "Weight"
            });

            categories.Add(appearanceCategory);

            // Hair category
            var hairCategory = new CustomizationCategory
            {
                categoryName = "Hair",
                iconPath = "Icons/Hair"
            };

            for (int i = 0; i < hairStyles.Count; i++)
            {
                hairCategory.options.Add(new CustomizationOption
                {
                    optionName = $"HairStyle_{i}",
                    displayName = $"Style {i + 1}",
                    prefab = hairStyles[i],
                    isUnlocked = true
                });
            }

            categories.Add(hairCategory);

            // Equipment category
            var equipmentCategory = new CustomizationCategory
            {
                categoryName = "Equipment",
                iconPath = "Icons/Equipment"
            };

            foreach (var armorSet in armorSets)
            {
                equipmentCategory.options.Add(new CustomizationOption
                {
                    optionName = armorSet.setName,
                    displayName = armorSet.setName,
                    prefab = armorSet.armorPrefab,
                    material = armorSet.armorMaterial,
                    isUnlocked = true
                });
            }

            categories.Add(equipmentCategory);
        }

        /// <summary>
        /// Create category buttons in the UI
        /// </summary>
        private void CreateCategoryButtons()
        {
            if (categoryButtonParent == null || categoryButtonPrefab == null) return;

            // Clear existing buttons
            foreach (Transform child in categoryButtonParent)
            {
                Destroy(child.gameObject);
            }

            // Create button for each category
            foreach (var category in categories)
            {
                var buttonGO = Instantiate(categoryButtonPrefab, categoryButtonParent);
                var button = buttonGO.GetComponent<Button>();
                var buttonText = buttonGO.GetComponentInChildren<TextMeshProUGUI>();

                if (buttonText != null)
                {
                    buttonText.text = category.categoryName;
                }

                if (button != null)
                {
                    button.onClick.AddListener(() => SetActiveCategory(category));
                }
            }
        }

        /// <summary>
        /// Set the active customization category
        /// </summary>
        public void SetActiveCategory(CustomizationCategory category)
        {
            activeCategory = category;
            OnCategoryChanged?.Invoke(category.categoryName);

            // Update category UI
            UpdateCategoryUI(category);
        }

        /// <summary>
        /// Update UI for the selected category
        /// </summary>
        private void UpdateCategoryUI(CustomizationCategory category)
        {
            // This would update the UI to show options for the selected category
            // Implementation depends on specific UI setup
            Debug.Log($"Showing category: {category.categoryName}");
        }

        /// <summary>
        /// Create character preview model
        /// </summary>
        private void CreateCharacterPreview()
        {
            if (characterBasePrefab == null || characterPreviewTransform == null) return;

            // Spawn character preview
            currentCharacter = Instantiate(characterBasePrefab, characterPreviewTransform);
            currentCharacter.name = "CharacterPreview";

            // Get components
            characterRenderer = currentCharacter.GetComponentInChildren<SkinnedMeshRenderer>();
            characterAnimator = currentCharacter.GetComponentInChildren<Animator>();

            // Apply initial character data
            ApplyCharacterData(currentCharacterData);

            // Start preview animations
            if (autoRotatePreview)
            {
                StartCoroutine(RotateCharacterPreview());
            }

            StartAnimationPreview();
        }

        /// <summary>
        /// Setup hand controllers for VR interaction
        /// </summary>
        private void SetupHandControllers()
        {
            var controllers = FindObjectsOfType<VRHandController>();
            foreach (var controller in controllers)
            {
                if (controller.handSide == XRNode.LeftHand)
                    leftHandController = controller;
                else if (controller.handSide == XRNode.RightHand)
                    rightHandController = controller;
            }

            // Setup interaction events
            if (leftHandController != null)
            {
                leftHandController.OnGestureDetected += HandleHandGesture;
            }

            if (rightHandController != null)
            {
                rightHandController.OnGestureDetected += HandleHandGesture;
            }
        }

        /// <summary>
        /// Generate unique character ID
        /// </summary>
        private void GenerateCharacterId()
        {
            currentCharacterData.characterId = System.Guid.NewGuid().ToString();
        }

        /// <summary>
        /// Handle hand gestures for character customization
        /// </summary>
        private void HandleHandGesture(string gestureName, Vector3 position, Quaternion rotation)
        {
            switch (gestureName)
            {
                case "point":
                    HandlePointGesture(position);
                    break;
                case "grab":
                    HandleGrabGesture(position);
                    break;
                case "thumbsUp":
                    SaveCharacter();
                    break;
            }
        }

        /// <summary>
        /// Handle point gesture for selecting options
        /// </summary>
        private void HandlePointGesture(Vector3 position)
        {
            // Raycast from hand position to detect UI elements
            Ray ray = new Ray(position, Vector3.forward);
            RaycastHit hit;

            if (Physics.Raycast(ray, out hit, 10f))
            {
                var selectable = hit.collider.GetComponent<ISelectable>();
                if (selectable != null)
                {
                    selectable.Select();
                }
            }
        }

        /// <summary>
        /// Handle grab gesture for manipulating character
        /// </summary>
        private void HandleGrabGesture(Vector3 position)
        {
            // Allow grabbing and rotating the character preview
            if (currentCharacter != null)
            {
                // Implementation for character manipulation
            }
        }

        /// <summary>
        /// Apply character data to the preview model
        /// </summary>
        public void ApplyCharacterData(CharacterData data)
        {
            if (currentCharacter == null) return;

            // Apply body morphs
            ApplyBodyMorphs(data);

            // Apply appearance materials
            ApplyAppearanceMaterials(data);

            // Apply hair style
            ApplyHairStyle(data);

            // Apply equipment
            ApplyEquipment(data);

            // Update character animator
            UpdateAnimator(data);
        }

        /// <summary>
        /// Apply body morphs (height, muscle, weight)
        /// </summary>
        private void ApplyBodyMorphs(CharacterData data)
        {
            if (currentCharacter == null) return;

            // Scale character based on height
            Vector3 scale = currentCharacter.transform.localScale;
            scale.y = data.height;
            currentCharacter.transform.localScale = scale;

            // Apply muscle and weight morphs if blend shapes are available
            if (characterRenderer != null && characterRenderer.sharedMesh != null)
            {
                // Muscle morph
                int muscleBlendShape = characterRenderer.sharedMesh.GetBlendShapeIndex("Muscle");
                if (muscleBlendShape >= 0)
                {
                    characterRenderer.SetBlendShapeWeight(muscleBlendShape, data.muscle * 100f);
                }

                // Weight morph
                int weightBlendShape = characterRenderer.sharedMesh.GetBlendShapeIndex("Weight");
                if (weightBlendShape >= 0)
                {
                    characterRenderer.SetBlendShapeWeight(weightBlendShape, data.weight * 100f);
                }
            }
        }

        /// <summary>
        /// Apply appearance materials
        /// </summary>
        private void ApplyAppearanceMaterials(CharacterData data)
        {
            if (characterRenderer == null) return;

            // Apply skin material
            if (data.skinToneIndex < skinMaterials.Count)
            {
                characterRenderer.material = skinMaterials[data.skinToneIndex];
            }

            // Apply eye materials (assuming separate eye renderer)
            var eyeRenderer = currentCharacter.transform.Find("Eyes")?.GetComponent<SkinnedMeshRenderer>();
            if (eyeRenderer != null && data.eyeColorIndex < eyeMaterials.Count)
            {
                eyeRenderer.material = eyeMaterials[data.eyeColorIndex];
            }
        }

        /// <summary>
        /// Apply hair style to character
        /// </summary>
        private void ApplyHairStyle(CharacterData data)
        {
            // Remove existing hair
            var existingHair = currentCharacter.transform.Find("Hair");
            if (existingHair != null)
            {
                Destroy(existingHair.gameObject);
            }

            // Add new hair style
            if (data.hairStyleIndex < hairStyles.Count)
            {
                var hairGO = Instantiate(hairStyles[data.hairStyleIndex], currentCharacter.transform);
                hairGO.name = "Hair";

                // Apply hair color
                var hairRenderer = hairGO.GetComponentInChildren<Renderer>();
                if (hairRenderer != null && data.hairColorIndex < hairMaterials.Count)
                {
                    hairRenderer.material = hairMaterials[data.hairColorIndex];
                }
            }
        }

        /// <summary>
        /// Apply equipment to character
        /// </summary>
        private void ApplyEquipment(CharacterData data)
        {
            // Clear existing equipment
            ClearEquipment();

            // Apply equipped items
            foreach (var equipment in data.equippedItems)
            {
                EquipItem(equipment.Key, equipment.Value);
            }
        }

        /// <summary>
        /// Equip an item to a specific slot
        /// </summary>
        public void EquipItem(string slotName, string itemName)
        {
            var slot = equipmentSlots.FirstOrDefault(s => s.slotName == slotName);
            if (slot == null) return;

            // Find item in available equipment
            var armorSet = armorSets.FirstOrDefault(a => a.setName == itemName);
            if (armorSet != null)
            {
                // Remove current equipment
                if (slot.currentEquipment != null)
                {
                    Destroy(slot.currentEquipment);
                }

                // Equip new item
                var equipmentGO = Instantiate(armorSet.armorPrefab, slot.slotTransform);
                equipmentGO.transform.localPosition = Vector3.zero;
                equipmentGO.transform.localRotation = Quaternion.identity;

                slot.currentEquipment = equipmentGO;
                currentEquipment[slotName] = itemName;

                // Apply material
                var renderer = equipmentGO.GetComponent<Renderer>();
                if (renderer != null && armorSet.armorMaterial != null)
                {
                    renderer.material = armorSet.armorMaterial;
                }
            }
        }

        /// <summary>
        /// Clear all equipped items
        /// </summary>
        private void ClearEquipment()
        {
            foreach (var slot in equipmentSlots)
            {
                if (slot.currentEquipment != null)
                {
                    Destroy(slot.currentEquipment);
                    slot.currentEquipment = null;
                }
            }

            currentEquipment.Clear();
        }

        /// <summary>
        /// Update character animator
        /// </summary>
        private void UpdateAnimator(CharacterData data)
        {
            if (characterAnimator == null) return;

            // Set animator parameters based on character class
            characterAnimator.SetInteger("Class", (int)data.characterClass);
            characterAnimator.SetInteger("Race", (int)data.race);
            characterAnimator.SetInteger("Gender", (int)data.gender);
        }

        /// <summary>
        /// Initialize equipment slots
        /// </summary>
        private void InitializeEquipmentSlots()
        {
            // Auto-detect equipment slots if not manually assigned
            if (equipmentSlots.Count == 0)
            {
                var slots = currentCharacter.GetComponentsInChildren<Transform>()
                    .Where(t => t.name.StartsWith("Slot_"))
                    .ToList();

                foreach (var slotTransform in slots)
                {
                    string slotName = slotTransform.name.Replace("Slot_", "");
                    EquipmentType type = ParseEquipmentType(slotName);

                    equipmentSlots.Add(new EquipmentSlot
                    {
                        slotName = slotName,
                        slotTransform = slotTransform,
                        type = type
                    });
                }
            }
        }

        /// <summary>
        /// Parse equipment type from string
        /// </summary>
        private EquipmentType ParseEquipmentType(string slotName)
        {
            switch (slotName.ToLower())
            {
                case "helmet":
                case "head":
                    return EquipmentType.Helmet;
                case "chest":
                case "chestplate":
                    return EquipmentType.Chestplate;
                case "gloves":
                case "hands":
                    return EquipmentType.Gloves;
                case "boots":
                case "feet":
                    return EquipmentType.Boots;
                case "belt":
                    return EquipmentType.Belt;
                case "cloak":
                case "cape":
                    return EquipmentType.Cloak;
                case "weapon":
                case "mainhand":
                    return EquipmentType.Weapon;
                case "shield":
                case "offhand":
                    return EquipmentType.Shield;
                default:
                    return EquipmentType.Chestplate;
            }
        }

        /// <summary>
        /// Start animation preview
        /// </summary>
        private void StartAnimationPreview()
        {
            if (animationPreviewCoroutine != null)
            {
                StopCoroutine(animationPreviewCoroutine);
            }

            animationPreviewCoroutine = StartCoroutine(AnimationPreviewRoutine());
        }

        /// <summary>
        /// Animation preview coroutine
        /// </summary>
        private IEnumerator AnimationPreviewRoutine()
        {
            if (characterAnimator == null || previewAnimations.Count == 0)
                yield break;

            int currentAnimationIndex = 0;

            while (true)
            {
                // Play current animation
                var clip = previewAnimations[currentAnimationIndex];
                characterAnimator.Play(clip.name);

                // Wait for animation to finish
                yield return new WaitForSeconds(clip.length);

                // Move to next animation
                currentAnimationIndex = (currentAnimationIndex + 1) % previewAnimations.Count;

                // Wait a bit between animations
                yield return new WaitForSeconds(1f);
            }
        }

        /// <summary>
        /// Rotate character preview automatically
        /// </summary>
        private IEnumerator RotateCharacterPreview()
        {
            while (currentCharacter != null)
            {
                if (characterPreviewTransform != null)
                {
                    characterPreviewTransform.Rotate(0f, rotationSpeed * Time.deltaTime, 0f);
                }
                yield return null;
            }
        }

        /// <summary>
        /// Handle input for character customization
        /// </summary>
        private void HandleInput()
        {
            // Handle controller input for adjusting values
            if (rightHandController != null)
            {
                // Use controller joystick/thumbstick for adjusting sliders
                Vector2 input = rightHandController.GetPrimary2DAxis();

                if (Mathf.Abs(input.x) > 0.1f)
                {
                    AdjustCurrentOption(input.x * 0.01f);
                }
            }
        }

        /// <summary>
        /// Adjust current customization option
        /// </summary>
        private void AdjustCurrentOption(float delta)
        {
            if (activeCategory == null) return;

            // Adjust based on active category
            switch (activeCategory.categoryName)
            {
                case "Appearance":
                    AdjustAppearanceOption(delta);
                    break;
                case "Hair":
                    AdjustHairOption(delta);
                    break;
            }
        }

        /// <summary>
        /// Adjust appearance option
        /// </summary>
        private void AdjustAppearanceOption(float delta)
        {
            // Cycle through appearance options
            // Implementation depends on specific UI system
        }

        /// <summary>
        /// Adjust hair option
        /// </summary>
        private void AdjustHairOption(float delta)
        {
            // Cycle through hair styles
            currentCharacterData.hairStyleIndex = Mathf.Clamp(
                currentCharacterData.hairStyleIndex + Mathf.RoundToInt(delta),
                0, hairStyles.Count - 1);

            ApplyCharacterData(currentCharacterData);
        }

        /// <summary>
        /// Update preview rotation
        /// </summary>
        private void UpdatePreviewRotation()
        {
            // Allow manual rotation with hand controllers
            if (rightHandController != null && rightHandController.IsGrabbing())
            {
                // Rotate character based on hand movement
                Vector3 handPosition = rightHandController.transform.position;
                // Implementation for manual rotation
            }
        }

        /// <summary>
        /// Randomize character appearance
        /// </summary>
        public void RandomizeCharacter()
        {
            currentCharacterData.race = (CharacterRace)Random.Range(0, System.Enum.GetValues(typeof(CharacterRace)).Length);
            currentCharacterData.characterClass = (CharacterClass)Random.Range(0, System.Enum.GetValues(typeof(CharacterClass)).Length);
            currentCharacterData.gender = (Gender)Random.Range(0, System.Enum.GetValues(typeof(Gender)).Length);
            currentCharacterData.height = Random.Range(minHeight, maxHeight);
            currentCharacterData.muscle = Random.Range(minMuscle, maxMuscle);
            currentCharacterData.weight = Random.Range(minWeight, maxWeight);
            currentCharacterData.skinToneIndex = Random.Range(0, skinMaterials.Count);
            currentCharacterData.hairStyleIndex = Random.Range(0, hairStyles.Count);
            currentCharacterData.hairColorIndex = Random.Range(0, hairMaterials.Count);
            currentCharacterData.eyeColorIndex = Random.Range(0, eyeMaterials.Count);

            ApplyCharacterData(currentCharacterData);
            OnCharacterUpdated?.Invoke(currentCharacterData);
        }

        /// <summary>
        /// Reset character to default settings
        /// </summary>
        public void ResetCharacter()
        {
            currentCharacterData = new CharacterData
            {
                characterName = "New Character",
                race = CharacterRace.Human,
                characterClass = CharacterClass.Fighter,
                gender = Gender.Male,
                height = 1.8f,
                muscle = 0.5f,
                weight = 0.5f
            };

            GenerateCharacterId();
            ApplyCharacterData(currentCharacterData);
            OnCharacterUpdated?.Invoke(currentCharacterData);
        }

        /// <summary>
        /// Save character data
        /// </summary>
        public void SaveCharacter()
        {
            if (string.IsNullOrEmpty(currentCharacterData.characterName))
            {
                currentCharacterData.characterName = "Character_" + Random.Range(1000, 9999);
            }

            // Save to backend or local storage
            StartCoroutine(SaveCharacterCoroutine());

            OnCharacterCreated?.Invoke(currentCharacterData);
            Debug.Log($"Character saved: {currentCharacterData.characterName}");
        }

        /// <summary>
        /// Save character coroutine
        /// </summary>
        private IEnumerator SaveCharacterCoroutine()
        {
            // Serialize character data
            string json = JsonUtility.ToJson(currentCharacterData, true);

            // Send to backend (placeholder implementation)
            WWWForm form = new WWWForm();
            form.AddField("characterData", json);

            // Simulate network request
            yield return new WaitForSeconds(1f);

            Debug.Log("Character data saved to backend");
        }

        /// <summary>
        /// Load character data
        /// </summary>
        public void LoadCharacter(string characterId)
        {
            StartCoroutine(LoadCharacterCoroutine(characterId));
        }

        /// <summary>
        /// Load character coroutine
        /// </summary>
        private IEnumerator LoadCharacterCoroutine(string characterId)
        {
            // Simulate loading from backend
            yield return new WaitForSeconds(1f);

            // In a real implementation, this would load from a server
            // For now, we'll just create a new character
            currentCharacterData.characterId = characterId;
            ApplyCharacterData(currentCharacterData);
            OnCharacterUpdated?.Invoke(currentCharacterData);
        }

        /// <summary>
        /// Get current character data
        /// </summary>
        public CharacterData GetCharacterData()
        {
            return currentCharacterData;
        }

        /// <summary>
        /// Set character name
        /// </summary>
        public void SetCharacterName(string name)
        {
            currentCharacterData.characterName = name;
            if (characterNameText != null)
            {
                characterNameText.text = name;
            }
        }

        /// <summary>
        /// Set character race
        /// </summary>
        public void SetCharacterRace(CharacterRace race)
        {
            currentCharacterData.race = race;
            ApplyCharacterData(currentCharacterData);
            OnCharacterUpdated?.Invoke(currentCharacterData);
        }

        /// <summary>
        /// Set character class
        /// </summary>
        public void SetCharacterClass(CharacterClass characterClass)
        {
            currentCharacterData.characterClass = characterClass;
            ApplyCharacterData(currentCharacterData);
            OnCharacterUpdated?.Invoke(currentCharacterData);
        }

        /// <summary>
        /// Enter character creation mode
        /// </summary>
        public void EnterCreationMode()
        {
            isCreatingCharacter = true;
            if (customizationPanel != null)
            {
                customizationPanel.SetActive(true);
            }
        }

        /// <summary>
        /// Exit character creation mode
        /// </summary>
        public void ExitCreationMode()
        {
            isCreatingCharacter = false;
            if (customizationPanel != null)
            {
                customizationPanel.SetActive(false);
            }
        }

        private void OnDestroy()
        {
            // Cleanup coroutines
            if (animationPreviewCoroutine != null)
            {
                StopCoroutine(animationPreviewCoroutine);
            }

            // Cleanup hand controller events
            if (leftHandController != null)
            {
                leftHandController.OnGestureDetected -= HandleHandGesture;
            }

            if (rightHandController != null)
            {
                rightHandController.OnGestureDetected -= HandleHandGesture;
            }

            // Cleanup character preview
            if (currentCharacter != null)
            {
                Destroy(currentCharacter);
            }
        }
    }

    /// <summary>
    /// Interface for selectable UI elements
    /// </summary>
    public interface ISelectable
    {
        void Select();
    }
}