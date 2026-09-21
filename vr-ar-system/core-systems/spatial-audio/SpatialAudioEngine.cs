using UnityEngine;
using UnityEngine.Audio;
using System.Collections.Generic;
using System.Collections;
using System.Linq;

namespace DMLog.VR
{
    /// <summary>
    /// Revolutionary Spatial Audio Engine for 360° Immersive Sound
    /// Features positional audio, environmental acoustics, and voice chat integration
    /// </summary>
    public class SpatialAudioEngine : MonoBehaviour
    {
        [Header("Audio Configuration")]
        [SerializeField] private AudioMixerGroup masterMixerGroup;
        [SerializeField] private AudioMixerGroup sfxMixerGroup;
        [SerializeField] private AudioMixerGroup voiceMixerGroup;
        [SerializeField] private AudioMixerGroup musicMixerGroup;
        [SerializeField] private AudioMixerGroup ambientMixerGroup;

        [Header("Spatial Audio Settings")]
        [SerializeField] private bool enableSpatialAudio = true;
        [SerializeField] private float maxAudioDistance = 50f;
        [SerializeField] private AudioRolloffMode rolloffMode = AudioRolloffMode.Logarithmic;
        [SerializeField] private float dopplerFactor = 1f;
        [SerializeField] private bool enableOcclusion = true;

        [Header("Voice Chat Settings")]
        [SerializeField] private bool enableVoiceChat = true;
        [SerializeField] private int maxVoiceChannels = 8;
        [SerializeField] private float voiceChatRange = 20f;
        [SerializeField] private bool enableVoiceSpatialization = true;
        [SerializeField] private float voiceAttenuation = 0.5f;

        [Header("Environmental Audio")]
        [SerializeField] private bool enableEnvironmentalAudio = true;
        [SerializeField] private EnvironmentType currentEnvironment = EnvironmentType.Forest;
        [SerializeField] private List<EnvironmentPreset> environmentPresets = new List<EnvironmentPreset>();

        [Header("Audio Pool Settings")]
        [SerializeField] private int sfxPoolSize = 50;
        [SerializeField] private int ambientPoolSize = 10;
        [SerializeField] private bool poolSounds = true;

        // Private state
        private Dictionary<string, AudioSource> activeAudioSources = new Dictionary<string, AudioSource>();
        private Queue<AudioSource> sfxAudioPool = new Queue<AudioSource>();
        private Queue<AudioSource> ambientAudioPool = new Queue<AudioSource>();
        private Dictionary<int, VoiceChatSource> voiceChatSources = new Dictionary<int, VoiceChatSource>();
        private List<AudioOccluder> occluders = new List<AudioOccluder>();
        private AudioReverbZone currentReverbZone;
        private Transform audioListenerTransform;
        private float masterVolume = 1f;
        private float sfxVolume = 1f;
        private float voiceVolume = 1f;
        private float musicVolume = 1f;
        private float ambientVolume = 1f;

        // Events
        public System.Action<string> OnSoundPlayed;
        public System.Action<int> OnVoiceChatStarted;
        public System.Action<int> OnVoiceChatEnded;
        public System.Action<EnvironmentType> OnEnvironmentChanged;

        public enum EnvironmentType
        {
            Outdoor, Indoor, Cave, Dungeon, Forest, Castle, Tavern, Battlefield, Custom
        }

        [System.Serializable]
        public class EnvironmentPreset
        {
            public EnvironmentType type;
            public string presetName;
            public AudioReverbPreset reverbPreset;
            public float reverbIntensity = 1f;
            public float damping = 1f;
            public float decayTime = 1.5f;
            public float roomSize = 1f;
            public float ambientVolume = 0.3f;
            public AudioClip ambientSound;
            public bool enableWeatherEffects = false;
            public AudioClip windSound;
            public AudioClip rainSound;
            public AudioClip thunderSound;
        }

        [System.Serializable]
        public class VoiceChatSource
        {
            public int playerId;
            public AudioSource audioSource;
            public Transform followTransform;
            public bool isActive;
            public float currentVolume;
            public Vector3 lastKnownPosition;
        }

        [System.Serializable]
        public class AudioOccluder
        {
            public GameObject occluder;
            public LayerMask occlusionLayer;
            public float occlusionFactor = 0.5f;
        }

        [System.Serializable]
        public class SoundEffect
        {
            public string effectName;
            public AudioClip[] audioClips;
            public float volume = 1f;
            public float pitchRange = 0.1f;
            public bool loop = false;
            public bool spatialBlend = true;
            public float minDistance = 1f;
            public float maxDistance = 20f;
        }

        private void Awake()
        {
            InitializeAudioEngine();
        }

        private void Start()
        {
            SetupAudioListener();
            InitializeAudioPools();
            LoadEnvironmentPresets();
            StartCoroutine(UpdateSpatialAudio());
        }

        /// <summary>
        /// Initialize the spatial audio engine
        /// </summary>
        private void InitializeAudioEngine()
        {
            Debug.Log("Initializing Spatial Audio Engine");

            // Create audio mixer if not assigned
            if (masterMixerGroup == null)
            {
                CreateDefaultAudioMixer();
            }

            // Initialize audio settings
            AudioConfiguration config = AudioSettings.GetConfiguration();
            config.dspBufferSize = 512; // Lower latency for VR
            AudioSettings.Reset(config);

            Debug.Log("Spatial Audio Engine initialized");
        }

        /// <summary>
        /// Setup audio listener for VR
        /// </summary>
        private void SetupAudioListener()
        {
            // Find or create audio listener
            var listener = FindObjectOfType<AudioListener>();
            if (listener == null)
            {
                var listenerGO = new GameObject("VR Audio Listener");
                listener = listenerGO.AddComponent<AudioListener>();
            }

            audioListenerTransform = listener.transform;

            // Attach to camera or XR rig
            var camera = Camera.main;
            if (camera != null)
            {
                audioListenerTransform.SetParent(camera.transform);
                audioListenerTransform.localPosition = Vector3.zero;
            }
        }

        /// <summary>
        /// Initialize audio source pools
        /// </summary>
        private void InitializeAudioPools()
        {
            if (!poolSounds) return;

            // Create SFX audio pool
            for (int i = 0; i < sfxPoolSize; i++)
            {
                var sfxSource = CreateAudioSource("SFX_Pooled_" + i, sfxMixerGroup);
                sfxSource.gameObject.SetActive(false);
                sfxAudioPool.Enqueue(sfxSource);
            }

            // Create ambient audio pool
            for (int i = 0; i < ambientPoolSize; i++)
            {
                var ambientSource = CreateAudioSource("Ambient_Pooled_" + i, ambientMixerGroup);
                ambientSource.gameObject.SetActive(false);
                ambientAudioPool.Enqueue(ambientSource);
            }

            Debug.Log($"Audio pools initialized: {sfxPoolSize} SFX, {ambientPoolSize} ambient");
        }

        /// <summary>
        /// Create a new audio source with default settings
        /// </summary>
        private AudioSource CreateAudioSource(string name, AudioMixerGroup mixerGroup)
        {
            var audioGO = new GameObject(name);
            audioGO.transform.SetParent(transform);

            var audioSource = audioGO.AddComponent<AudioSource>();
            audioSource.outputAudioMixerGroup = mixerGroup;
            audioSource.spatialBlend = 1f; // Full 3D spatial audio
            audioSource.rolloffMode = rolloffMode;
            audioSource.minDistance = 1f;
            audioSource.maxDistance = maxAudioDistance;
            audioSource.dopplerLevel = dopplerFactor;
            audioSource.playOnAwake = false;

            return audioSource;
        }

        /// <summary>
        /// Load default environment presets
        /// </summary>
        private void LoadEnvironmentPresets()
        {
            if (environmentPresets.Count > 0) return;

            // Forest environment
            environmentPresets.Add(new EnvironmentPreset
            {
                type = EnvironmentType.Forest,
                presetName = "Forest",
                reverbPreset = AudioReverbPreset.Forest,
                reverbIntensity = 0.7f,
                damping = 0.8f,
                decayTime = 2.2f,
                roomSize = 1.2f,
                ambientVolume = 0.4f,
                enableWeatherEffects = true,
                windSound = LoadAudioClip("forest_wind"),
                rainSound = LoadAudioClip("forest_rain")
            });

            // Dungeon environment
            environmentPresets.Add(new EnvironmentPreset
            {
                type = EnvironmentType.Dungeon,
                presetName = "Dungeon",
                reverbPreset = AudioReverbPreset.Cave,
                reverbIntensity = 1.2f,
                damping = 1.5f,
                decayTime = 3.0f,
                roomSize = 0.8f,
                ambientVolume = 0.2f,
                ambientSound = LoadAudioClip("dungeon_ambient")
            });

            // Tavern environment
            environmentPresets.Add(new EnvironmentPreset
            {
                type = EnvironmentType.Tavern,
                presetName = "Tavern",
                reverbPreset = AudioReverbPreset.Room,
                reverbIntensity = 0.5f,
                damping = 0.6f,
                decayTime = 1.0f,
                roomSize = 0.6f,
                ambientVolume = 0.3f,
                ambientSound = LoadAudioClip("tavern_ambient")
            });

            // Battlefield environment
            environmentPresets.Add(new EnvironmentPreset
            {
                type = EnvironmentType.Battlefield,
                presetName = "Battlefield",
                reverbPreset = AudioReverbPreset.Plain,
                reverbIntensity = 0.3f,
                damping = 0.4f,
                decayTime = 1.5f,
                roomSize = 2.0f,
                ambientVolume = 0.5f,
                enableWeatherEffects = true,
                windSound = LoadAudioClip("battlefield_wind")
            });

            Debug.Log($"Loaded {environmentPresets.Count} environment presets");
        }

        /// <summary>
        /// Create default audio mixer
        /// </summary>
        private void CreateDefaultAudioMixer()
        {
            // This would normally be created in the Unity Editor
            // For runtime creation, we'd use the AudioMixer API
            Debug.LogWarning("Audio Mixer not assigned - using default settings");
        }

        /// <summary>
        /// Load audio clip (placeholder implementation)
        /// </summary>
        private AudioClip LoadAudioClip(string clipName)
        {
            // In a real implementation, this would load from Resources or Addressables
            return null;
        }

        /// <summary>
        /// Main spatial audio update coroutine
        /// </summary>
        private IEnumerator UpdateSpatialAudio()
        {
            while (true)
            {
                UpdateVoiceChatSources();
                UpdateEnvironmentalAudio();
                UpdateAudioOcclusion();
                UpdateAudioLevels();

                yield return new WaitForSeconds(0.1f); // Update 10 times per second
            }
        }

        /// <summary>
        /// Update voice chat sources with spatial positioning
        /// </summary>
        private void UpdateVoiceChatSources()
        {
            if (!enableVoiceChat) return;

            foreach (var voiceSource in voiceChatSources.Values.ToList())
            {
                if (!voiceSource.isActive) continue;

                // Update voice source position
                if (voiceSource.followTransform != null)
                {
                    voiceSource.lastKnownPosition = voiceSource.followTransform.position;
                }

                // Calculate distance-based volume attenuation
                if (enableVoiceSpatialization && audioListenerTransform != null)
                {
                    float distance = Vector3.Distance(voiceSource.lastKnownPosition, audioListenerTransform.position);
                    float distanceAttenuation = 1f - Mathf.Clamp01(distance / voiceChatRange);

                    // Apply occlusion
                    float occlusionFactor = CalculateOcclusion(voiceSource.lastKnownPosition, audioListenerTransform.position);

                    // Update volume
                    voiceSource.currentVolume = voiceVolume * distanceAttenuation * occlusionFactor;
                    voiceSource.audioSource.volume = voiceSource.currentVolume;

                    // Update spatial blend
                    if (distance < 2f)
                    {
                        voiceSource.audioSource.spatialBlend = 0.3f; // Less spatial when very close
                    }
                    else
                    {
                        voiceSource.audioSource.spatialBlend = 1f; // Full spatial
                    }
                }
            }
        }

        /// <summary>
        /// Update environmental audio based on current environment
        /// </summary>
        private void UpdateEnvironmentalAudio()
        {
            if (!enableEnvironmentalAudio) return;

            var currentPreset = environmentPresets.FirstOrDefault(p => p.type == currentEnvironment);
            if (currentPreset == null) return;

            // Update ambient audio
            // This would handle playing environment-specific sounds
            // and weather effects based on the current preset
        }

        /// <summary>
        /// Update audio occlusion calculations
        /// </summary>
        private void UpdateAudioOcclusion()
        {
            if (!enableOcclusion) return;

            // Update occlusion for all active audio sources
            foreach (var audioSource in activeAudioSources.Values)
            {
                if (audioSource == null || !audioSource.isPlaying) continue;

                if (audioListenerTransform != null)
                {
                    float occlusionFactor = CalculateOcclusion(audioSource.transform.position, audioListenerTransform.position);

                    // Apply occlusion to volume
                    audioSource.volume *= occlusionFactor;

                    // Apply low-pass filter for muffled sound through walls
                    // This would require audio filter components
                }
            }
        }

        /// <summary>
        /// Update audio levels based on current settings
        /// </summary>
        private void UpdateAudioLevels()
        {
            // Update mixer group volumes
            if (masterMixerGroup != null)
            {
                masterMixerGroup.audioMixer.SetFloat("MasterVolume", Mathf.Log10(masterVolume) * 20);
            }

            if (sfxMixerGroup != null)
            {
                sfxMixerGroup.audioMixer.SetFloat("SFXVolume", Mathf.Log10(sfxVolume) * 20);
            }

            if (voiceMixerGroup != null)
            {
                voiceMixerGroup.audioMixer.SetFloat("VoiceVolume", Mathf.Log10(voiceVolume) * 20);
            }

            if (musicMixerGroup != null)
            {
                musicMixerGroup.audioMixer.SetFloat("MusicVolume", Mathf.Log10(musicVolume) * 20);
            }

            if (ambientMixerGroup != null)
            {
                ambientMixerGroup.audioMixer.SetFloat("AmbientVolume", Mathf.Log10(ambientVolume) * 20);
            }
        }

        /// <summary>
        /// Calculate occlusion factor between two points
        /// </summary>
        private float CalculateOcclusion(Vector3 sourcePos, Vector3 listenerPos)
        {
            if (!enableOcclusion) return 1f;

            float totalOcclusion = 1f;

            // Raycast from source to listener
            Vector3 direction = listenerPos - sourcePos;
            float distance = direction.magnitude;

            if (Physics.Raycast(sourcePos, direction.normalized, out RaycastHit hit, distance))
            {
                // Calculate occlusion based on hit object
                totalOcclusion *= 0.5f; // Reduce volume by 50% when occluded
            }

            return Mathf.Clamp(totalOcclusion, 0.1f, 1f);
        }

        /// <summary>
        /// Play a spatial sound effect at a specific position
        /// </summary>
        public void PlaySpatialSound(string soundName, Vector3 position, SoundEffect soundEffect = null)
        {
            if (soundEffect == null)
            {
                soundEffect = GetSoundEffect(soundName);
                if (soundEffect == null)
                {
                    Debug.LogWarning($"Sound effect not found: {soundName}");
                    return;
                }
            }

            AudioSource audioSource = GetPooledAudioSource(sfxAudioPool);
            if (audioSource == null)
            {
                audioSource = CreateAudioSource("Dynamic_SFX", sfxMixerGroup);
            }

            // Configure audio source
            audioSource.transform.position = position;
            audioSource.clip = soundEffect.audioClips[Random.Range(0, soundEffect.audioClips.Length)];
            audioSource.volume = soundEffect.volume * sfxVolume;
            audioSource.pitch = 1f + Random.Range(-soundEffect.pitchRange, soundEffect.pitchRange);
            audioSource.loop = soundEffect.loop;
            audioSource.spatialBlend = soundEffect.spatialBlend ? 1f : 0f;
            audioSource.minDistance = soundEffect.minDistance;
            audioSource.maxDistance = soundEffect.maxDistance;

            // Play sound
            audioSource.Play();

            // Store active source
            activeAudioSources[soundName + "_" + Time.time] = audioSource;

            // Schedule cleanup for non-looping sounds
            if (!soundEffect.loop)
            {
                StartCoroutine(CleanupAudioSource(audioSource, audioSource.clip.length));
            }

            OnSoundPlayed?.Invoke(soundName);
        }

        /// <summary>
        /// Play a spell sound effect with enhanced spatial positioning
        /// </summary>
        public void PlaySpellSound(string spellName, Vector3 castPosition, Vector3 targetPosition)
        {
            // Play cast sound at caster position
            PlaySpatialSound($"spell_cast_{spellName}", castPosition);

            // Play impact sound at target position
            PlaySpatialSound($"spell_impact_{spellName}", targetPosition);

            // Add environmental reverb based on distance
            float distance = Vector3.Distance(castPosition, targetPosition);
            if (distance > 10f)
            {
                // Play echo/delayed sound for distant effects
                StartCoroutine(PlayDelayedSound(spellName, targetPosition, distance / 343f)); // Speed of sound
            }
        }

        /// <summary>
        /// Play delayed sound for distance-based effects
        /// </summary>
        private IEnumerator PlayDelayedSound(string spellName, Vector3 position, float delay)
        {
            yield return new WaitForSeconds(delay);
            PlaySpatialSound($"spell_echo_{spellName}", position);
        }

        /// <summary>
        /// Start voice chat for a player
        /// </summary>
        public void StartVoiceChat(int playerId, Transform followTransform = null)
        {
            if (voiceChatSources.ContainsKey(playerId))
            {
                // Update existing voice chat source
                var existingSource = voiceChatSources[playerId];
                existingSource.followTransform = followTransform;
                existingSource.isActive = true;
                return;
            }

            // Create new voice chat source
            var voiceSource = new GameObject($"VoiceChat_{playerId}");
            voiceSource.transform.SetParent(transform);

            var audioSource = voiceSource.AddComponent<AudioSource>();
            audioSource.outputAudioMixerGroup = voiceMixerGroup;
            audioSource.spatialBlend = 1f;
            audioSource.rolloffMode = AudioRolloffMode.Logarithmic;
            audioSource.minDistance = 1f;
            audioSource.maxDistance = voiceChatRange;
            audioSource.loop = true;

            var voiceChatSource = new VoiceChatSource
            {
                playerId = playerId,
                audioSource = audioSource,
                followTransform = followTransform,
                isActive = true,
                currentVolume = voiceVolume,
                lastKnownPosition = followTransform != null ? followTransform.position : Vector3.zero
            };

            voiceChatSources[playerId] = voiceChatSource;
            OnVoiceChatStarted?.Invoke(playerId);
        }

        /// <summary>
        /// Stop voice chat for a player
        /// </summary>
        public void StopVoiceChat(int playerId)
        {
            if (!voiceChatSources.ContainsKey(playerId)) return;

            var voiceSource = voiceChatSources[playerId];
            voiceSource.isActive = false;

            if (voiceSource.audioSource != null && voiceSource.audioSource.isPlaying)
            {
                voiceSource.audioSource.Stop();
            }

            OnVoiceChatEnded?.Invoke(playerId);
        }

        /// <summary>
        /// Change the current environment
        /// </summary>
        public void SetEnvironment(EnvironmentType environment)
        {
            if (currentEnvironment == environment) return;

            currentEnvironment = environment;
            var preset = environmentPresets.FirstOrDefault(p => p.type == environment);

            if (preset != null)
            {
                ApplyEnvironmentPreset(preset);
            }

            OnEnvironmentChanged?.Invoke(environment);
        }

        /// <summary>
        /// Apply environment preset to audio settings
        /// </summary>
        private void ApplyEnvironmentPreset(EnvironmentPreset preset)
        {
            // Create or update reverb zone
            if (currentReverbZone == null)
            {
                var reverbGO = new GameObject("Environment Reverb");
                reverbGO.transform.SetParent(transform);
                currentReverbZone = reverbGO.AddComponent<AudioReverbZone>();
            }

            currentReverbZone.reverbPreset = preset.reverbPreset;
            currentReverbZone.reverbIntensity = preset.reverbIntensity;
            currentReverbZone.damping = preset.damping;
            currentReverbZone.decayTime = preset.decayTime;
            currentReverbZone.roomSize = preset.roomSize;

            // Play ambient sound
            if (preset.ambientSound != null)
            {
                PlayAmbientSound(preset.ambientSound, preset.ambientVolume);
            }
        }

        /// <summary>
        /// Play ambient environmental sound
        /// </summary>
        private void PlayAmbientSound(AudioClip ambientClip, float volume)
        {
            AudioSource ambientSource = GetPooledAudioSource(ambientAudioPool);
            if (ambientSource == null)
            {
                ambientSource = CreateAudioSource("Ambient_Sound", ambientMixerGroup);
            }

            ambientSource.clip = ambientClip;
            ambientSource.volume = volume * ambientVolume;
            ambientSource.loop = true;
            ambientSource.spatialBlend = 0f; // Non-spatial ambient sound
            ambientSource.Play();

            activeAudioSources["ambient_" + Time.time] = ambientSource;
        }

        /// <summary>
        /// Get audio source from pool
        /// </summary>
        private AudioSource GetPooledAudioSource(Queue<AudioSource> pool)
        {
            if (pool.Count > 0)
            {
                var source = pool.Dequeue();
                source.gameObject.SetActive(true);
                return source;
            }
            return null;
        }

        /// <summary>
        /// Return audio source to pool
        /// </summary>
        private void ReturnToPool(AudioSource source, Queue<AudioSource> pool)
        {
            source.Stop();
            source.clip = null;
            source.gameObject.SetActive(false);
            pool.Enqueue(source);
        }

        /// <summary>
        /// Cleanup audio source after playback
        /// </summary>
        private IEnumerator CleanupAudioSource(AudioSource source, float delay)
        {
            yield return new WaitForSeconds(delay);

            source.Stop();

            // Remove from active sources
            var key = activeAudioSources.FirstOrDefault(kvp => kvp.Value == source).Key;
            if (!string.IsNullOrEmpty(key))
            {
                activeAudioSources.Remove(key);
            }

            // Return to pool
            if (sfxAudioPool.Count < sfxPoolSize)
            {
                ReturnToPool(source, sfxAudioPool);
            }
            else
            {
                Destroy(source.gameObject);
            }
        }

        /// <summary>
        /// Get sound effect by name (placeholder implementation)
        /// </summary>
        private SoundEffect GetSoundEffect(string soundName)
        {
            // This would normally load from a database or asset bundle
            return null;
        }

        /// <summary>
        /// Set master volume
        /// </summary>
        public void SetMasterVolume(float volume)
        {
            masterVolume = Mathf.Clamp01(volume);
        }

        /// <summary>
        /// Set SFX volume
        /// </summary>
        public void SetSFXVolume(float volume)
        {
            sfxVolume = Mathf.Clamp01(volume);
        }

        /// <summary>
        /// Set voice chat volume
        /// </summary>
        public void SetVoiceVolume(float volume)
        {
            voiceVolume = Mathf.Clamp01(volume);
        }

        /// <summary>
        /// Set music volume
        /// </summary>
        public void SetMusicVolume(float volume)
        {
            musicVolume = Mathf.Clamp01(volume);
        }

        /// <summary>
        /// Set ambient volume
        /// </summary>
        public void SetAmbientVolume(float volume)
        {
            ambientVolume = Mathf.Clamp01(volume);
        }

        /// <summary>
        /// Add audio occluder
        /// </summary>
        public void AddOccluder(GameObject occluder, LayerMask occlusionLayer, float occlusionFactor = 0.5f)
        {
            occluders.Add(new AudioOccluder
            {
                occluder = occluder,
                occlusionLayer = occlusionLayer,
                occlusionFactor = occlusionFactor
            });
        }

        /// <summary>
        /// Remove audio occluder
        /// </summary>
        public void RemoveOccluder(GameObject occluder)
        {
            occluders.RemoveAll(o => o.occluder == occluder);
        }

        private void OnDestroy()
        {
            // Cleanup all audio sources
            foreach (var source in activeAudioSources.Values)
            {
                if (source != null)
                {
                    Destroy(source.gameObject);
                }
            }

            // Cleanup voice chat sources
            foreach (var voiceSource in voiceChatSources.Values)
            {
                if (voiceSource.audioSource != null)
                {
                    Destroy(voiceSource.audioSource.gameObject);
                }
            }

            StopAllCoroutines();
        }
    }
}