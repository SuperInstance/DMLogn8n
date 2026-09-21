using UnityEngine;
using UnityEngine.Audio;
using System.Collections.Generic;
using System.Collections;

namespace DND.ARVR
{
    /// <summary>
    /// Spatial audio manager for D&D AR/VR experiences
    /// Handles 3D positioning, environmental audio, and voice chat
    /// </summary>
    public class SpatialAudioManager : MonoBehaviour
    {
        [Header("Audio Settings")]
        [SerializeField] private AudioMixerGroup masterMixerGroup;
        [SerializeField] private AudioMixerGroup sfxMixerGroup;
        [SerializeField] private AudioMixerGroup voiceMixerGroup;
        [SerializeField] private AudioMixerGroup ambientMixerGroup;
        [SerializeField] private float maxAudioDistance = 50f;
        [SerializeField] private float rolloffFactor = 1f;

        [Header("Ambient Audio")]
        [SerializeField] private AudioClip[] dungeonAmbientClips;
        [SerializeField] private AudioClip[] forestAmbientClips;
        [SerializeField] private AudioClip[] combatAmbientClips;
        [SerializeField] private AudioClip[] tavernAmbientClips;
        [SerializeField] private float ambientFadeTime = 2f;

        [Header("Spell Audio")]
        [SerializeField] private AudioClip[] spellCastClips;
        [SerializeField] private AudioClip[] spellHitClips;
        [SerializeField] private AudioClip[] spellMissClips;

        [Header("Dice Audio")]
        [SerializeField] private AudioClip[] diceRollClips;
        [SerializeField] private AudioClip[] diceImpactClips;

        [Header("Voice Chat")]
        [SerializeField] private int maxVoiceSources = 8;
        [SerializeField] private float voiceChatDistance = 20f;
        [SerializeField] private bool enableVoiceChat = true;

        [Header("Environmental Audio")]
        [SerializeField] private bool enableEnvironmentalAudio = true;
        [SerializeField] private float reverbZoneIntensity = 1f;
        [SerializeField] private AudioClip[] footstepClips;
        [SerializeField] private AudioClip[] armorClips;

        // Audio sources
        private AudioSource ambientAudioSource;
        private List<AudioSource> sfxAudioSources = new List<AudioSource>();
        private List<AudioSource> voiceAudioSources = new List<AudioSource>();
        private Dictionary<string, AudioReverbZone> reverbZones = new Dictionary<string, AudioReverbZone>();

        // State
        private EnvironmentType currentEnvironment = EnvironmentType.Dungeon;
        private bool isMuted = false;
        private float masterVolume = 1f;
        private float sfxVolume = 1f;
        private float voiceVolume = 1f;
        private float ambientVolume = 1f;

        // Voice chat
        private Dictionary<int, VoiceChatSource> voiceChatSources = new Dictionary<int, VoiceChatSource>();

        // Events
        public System.Action<string> OnAmbientChanged;
        public System.Action<float> OnVolumeChanged;

        private void Awake()
        {
            InitializeAudioSources();
            SetupAudioMixer();
        }

        private void Start()
        {
            PlayAmbientAudio(currentEnvironment);
        }

        private void Update()
        {
            UpdateVoiceChatPositions();
            UpdateEnvironmentalAudio();
        }

        private void InitializeAudioSources()
        {
            // Create ambient audio source
            var ambientGO = new GameObject("AmbientAudioSource");
            ambientGO.transform.SetParent(transform);
            ambientAudioSource = ambientGO.AddComponent<AudioSource>();
            ambientAudioSource.spatialBlend = 0f; // 2D sound
            ambientAudioSource.loop = true;
            ambientAudioSource.playOnAwake = false;

            // Create SFX audio sources pool
            for (int i = 0; i < 10; i++)
            {
                var sfxGO = new GameObject($"SFXAudioSource_{i}");
                sfxGO.transform.SetParent(transform);
                var sfxSource = sfxGO.AddComponent<AudioSource>();
                sfxSource.spatialBlend = 1f; // 3D sound
                sfxSource.rolloffMode = AudioRolloffMode.Logarithmic;
                sfxSource.minDistance = 1f;
                sfxSource.maxDistance = maxAudioDistance;
                sfxSource.playOnAwake = false;
                sfxAudioSources.Add(sfxSource);
            }

            // Create voice chat audio sources pool
            if (enableVoiceChat)
            {
                for (int i = 0; i < maxVoiceSources; i++)
                {
                    var voiceGO = new GameObject($"VoiceAudioSource_{i}");
                    voiceGO.transform.SetParent(transform);
                    var voiceSource = voiceGO.AddComponent<AudioSource>();
                    voiceSource.spatialBlend = 1f; // 3D sound
                    voiceSource.rolloffMode = AudioRolloffMode.Logarithmic;
                    voiceSource.minDistance = 0.5f;
                    voiceSource.maxDistance = voiceChatDistance;
                    voiceSource.playOnAwake = false;
                    voiceAudioSources.Add(voiceSource);
                }
            }
        }

        private void SetupAudioMixer()
        {
            // Set up audio mixer groups if assigned
            if (ambientAudioSource != null && ambientMixerGroup != null)
            {
                ambientAudioSource.outputAudioMixerGroup = ambientMixerGroup;
            }

            foreach (var source in sfxAudioSources)
            {
                if (sfxMixerGroup != null)
                {
                    source.outputAudioMixerGroup = sfxMixerGroup;
                }
            }

            foreach (var source in voiceAudioSources)
            {
                if (voiceMixerGroup != null)
                {
                    source.outputAudioMixerGroup = voiceMixerGroup;
                }
            }
        }

        public void PlayAmbientAudio(EnvironmentType environment)
        {
            if (ambientAudioSource == null) return;

            currentEnvironment = environment;
            AudioClip[] ambientClips = GetAmbientClips(environment);

            if (ambientClips == null || ambientClips.Length == 0) return;

            // Crossfade to new ambient
            StartCoroutine(CrossfadeAmbient(ambientClips[Random.Range(0, ambientClips.Length)]));

            OnAmbientChanged?.Invoke(environment.ToString());
        }

        private AudioClip[] GetAmbientClips(EnvironmentType environment)
        {
            return environment switch
            {
                EnvironmentType.Dungeon => dungeonAmbientClips,
                EnvironmentType.Forest => forestAmbientClips,
                EnvironmentType.Combat => combatAmbientClips,
                EnvironmentType.Tavern => tavernAmbientClips,
                _ => dungeonAmbientClips
            };
        }

        private IEnumerator CrossfadeAmbient(AudioClip newClip)
        {
            if (ambientAudioSource.isPlaying)
            {
                // Fade out current ambient
                float startVolume = ambientAudioSource.volume;
                float fadeTime = 0f;

                while (fadeTime < ambientFadeTime / 2f)
                {
                    fadeTime += Time.deltaTime;
                    ambientAudioSource.volume = Mathf.Lerp(startVolume, 0f, fadeTime / (ambientFadeTime / 2f));
                    yield return null;
                }

                ambientAudioSource.Stop();
            }

            // Start new ambient
            ambientAudioSource.clip = newClip;
            ambientAudioSource.Play();

            // Fade in new ambient
            float fadeInTime = 0f;
            while (fadeInTime < ambientFadeTime / 2f)
            {
                fadeInTime += Time.deltaTime;
                ambientAudioSource.volume = Mathf.Lerp(0f, ambientVolume, fadeInTime / (ambientFadeTime / 2f));
                yield return null;
            }
        }

        public AudioSource PlaySFX(AudioClip clip, Vector3 position, float volume = 1f, float pitch = 1f)
        {
            if (clip == null || sfxAudioSources.Count == 0) return null;

            AudioSource source = GetAvailableAudioSource(sfxAudioSources);
            if (source == null) return null;

            source.transform.position = position;
            source.clip = clip;
            source.volume = volume * sfxVolume;
            source.pitch = pitch;
            source.spatialBlend = 1f; // 3D sound
            source.Play();

            // Auto-cleanup when finished
            StartCoroutine(CleanupAudioSource(source, clip.length));

            return source;
        }

        public AudioSource PlaySpellAudio(SpellType spellType, Vector3 position, SpellAudioType audioType = SpellAudioType.Cast)
        {
            AudioClip clip = GetSpellClip(spellType, audioType);
            if (clip == null) return null;

            float pitch = GetSpellPitch(spellType);
            return PlaySFX(clip, position, 1f, pitch);
        }

        private AudioClip GetSpellClip(SpellType spellType, SpellAudioType audioType)
        {
            AudioClip[] clips = audioType switch
            {
                SpellAudioType.Cast => spellCastClips,
                SpellAudioType.Hit => spellHitClips,
                SpellAudioType.Miss => spellMissClips,
                _ => spellCastClips
            };

            if (clips == null || clips.Length == 0) return null;

            // Get clip based on spell type
            int index = (int)spellType % clips.Length;
            return clips[index];
        }

        private float GetSpellPitch(SpellType spellType)
        {
            return spellType switch
            {
                SpellType.Fireball => 0.8f,
                SpellType.Lightning => 1.2f,
                SpellType.Healing => 1.5f,
                SpellType.Shield => 1.0f,
                SpellType.Teleport => 0.6f,
                _ => 1.0f
            };
        }

        public AudioSource PlayDiceAudio(Vector3 position, DiceAudioType audioType = DiceAudioType.Roll)
        {
            AudioClip clip = GetDiceClip(audioType);
            if (clip == null) return null;

            float pitch = Random.Range(0.8f, 1.2f);
            return PlaySFX(clip, position, 0.5f, pitch);
        }

        private AudioClip GetDiceClip(DiceAudioType audioType)
        {
            AudioClip[] clips = audioType switch
            {
                DiceAudioType.Roll => diceRollClips,
                DiceAudioType.Impact => diceImpactClips,
                _ => diceRollClips
            };

            if (clips == null || clips.Length == 0) return null;
            return clips[Random.Range(0, clips.Length)];
        }

        public AudioSource PlayFootstepAudio(Vector3 position, SurfaceType surfaceType = SurfaceType.Stone)
        {
            if (footstepClips == null || footstepClips.Length == 0) return null;

            AudioClip clip = footstepClips[Random.Range(0, footstepClips.Length)];
            float pitch = GetFootstepPitch(surfaceType);
            return PlaySFX(clip, position, 0.3f, pitch);
        }

        private float GetFootstepPitch(SurfaceType surfaceType)
        {
            return surfaceType switch
            {
                SurfaceType.Stone => 1.0f,
                SurfaceType.Dirt => 0.8f,
                SurfaceType.Grass => 0.9f,
                SurfaceType.Wood => 1.1f,
                SurfaceType.Metal => 1.2f,
                _ => 1.0f
            };
        }

        public int StartVoiceChat(int playerId, Vector3 position)
        {
            if (!enableVoiceChat || voiceAudioSources.Count == 0) return -1;

            AudioSource source = GetAvailableAudioSource(voiceAudioSources);
            if (source == null) return -1;

            var voiceSource = new VoiceChatSource
            {
                playerId = playerId,
                audioSource = source,
                position = position,
                isActive = true
            };

            source.transform.position = position;
            source.volume = voiceVolume;
            source.spatialBlend = 1f;
            source.loop = true;

            voiceChatSources[playerId] = voiceSource;
            return playerId;
        }

        public void UpdateVoiceChatPosition(int playerId, Vector3 position)
        {
            if (!voiceChatSources.ContainsKey(playerId)) return;

            var voiceSource = voiceChatSources[playerId];
            voiceSource.position = position;
            voiceSource.audioSource.transform.position = position;
        }

        public void StopVoiceChat(int playerId)
        {
            if (!voiceChatSources.ContainsKey(playerId)) return;

            var voiceSource = voiceChatSources[playerId];
            voiceSource.audioSource.Stop();
            voiceSource.isActive = false;

            voiceChatSources.Remove(playerId);
        }

        private void UpdateVoiceChatPositions()
        {
            if (!enableVoiceChat) return;

            Vector3 listenerPosition = Camera.main != null ? Camera.main.transform.position : Vector3.zero;

            foreach (var kvp in voiceChatSources)
            {
                var voiceSource = kvp.Value;
                if (!voiceSource.isActive) continue;

                float distance = Vector3.Distance(listenerPosition, voiceSource.position);
                float volume = CalculateVolumeBasedOnDistance(distance, voiceChatDistance);

                voiceSource.audioSource.volume = volume * voiceVolume;
            }
        }

        private void UpdateEnvironmentalAudio()
        {
            if (!enableEnvironmentalAudio) return;

            // Update environmental audio based on player position
            // This could include different reverb zones, environmental sounds, etc.
        }

        public void CreateReverbZone(string name, Vector3 position, float radius, AudioReverbPreset preset)
        {
            var zoneGO = new GameObject($"ReverbZone_{name}");
            zoneGO.transform.position = position;
            zoneGO.transform.SetParent(transform);

            var reverbZone = zoneGO.AddComponent<AudioReverbZone>();
            reverbZone.minDistance = 0f;
            reverbZone.maxDistance = radius;
            reverbZone.reverbPreset = preset;
            reverbZone.room = room;
            reverbZone.roomHF = roomHF;
            reverbZone.decayTime = decayTime;
            reverbZone.decayHFRatio = decayHFRatio;
            reverbZone.reflectionsLevel = reflectionsLevel;
            reverbZone.reflectionsDelay = reflectionsDelay;
            reverbZone.reverbLevel = reverbLevel;
            reverbZone.reverbDelay = reverbDelay;
            reverbZone.diffusion = diffusion;
            reverbZone.density = density;
            reverbZone.HFReference = HFReference;
            reverbZone.roomLF = roomLF;
            reverbZone.LFReference = LFReference;

            reverbZones[name] = reverbZone;
        }

        private AudioSource GetAvailableAudioSource(List<AudioSource> sources)
        {
            foreach (var source in sources)
            {
                if (!source.isPlaying)
                {
                    return source;
                }
            }
            return null;
        }

        private IEnumerator CleanupAudioSource(AudioSource source, float delay)
        {
            yield return new WaitForSeconds(delay + 0.1f); // Small buffer time

            if (source != null && !source.isPlaying)
            {
                source.clip = null;
                source.Stop();
            }
        }

        private float CalculateVolumeBasedOnDistance(float distance, float maxDistance)
        {
            if (distance >= maxDistance) return 0f;

            // Logarithmic rolloff
            float volume = 1f / (1f + rolloffFactor * (distance - 1f));
            return Mathf.Max(0f, volume);
        }

        // Volume controls
        public void SetMasterVolume(float volume)
        {
            masterVolume = Mathf.Clamp01(volume);
            ApplyVolumeToMixer("MasterVolume", masterVolume);
            OnVolumeChanged?.Invoke(masterVolume);
        }

        public void SetSFXVolume(float volume)
        {
            sfxVolume = Mathf.Clamp01(volume);
            ApplyVolumeToMixer("SFXVolume", sfxVolume);
        }

        public void SetVoiceVolume(float volume)
        {
            voiceVolume = Mathf.Clamp01(volume);
            ApplyVolumeToMixer("VoiceVolume", voiceVolume);
        }

        public void SetAmbientVolume(float volume)
        {
            ambientVolume = Mathf.Clamp01(volume);
            ApplyVolumeToMixer("AmbientVolume", ambientVolume);
        }

        private void ApplyVolumeToMixer(string parameterName, float volume)
        {
            // Convert linear volume to decibels
            float dbVolume = volume > 0f ? 20f * Mathf.Log10(volume) : -80f;

            if (masterMixerGroup != null && masterMixerGroup.audioMixer != null)
            {
                masterMixerGroup.audioMixer.SetFloat(parameterName, dbVolume);
            }
        }

        public void MuteAll(bool mute)
        {
            isMuted = mute;
            AudioListener.pause = mute;

            if (masterMixerGroup != null && masterMixerGroup.audioMixer != null)
            {
                masterMixerGroup.audioMixer.SetFloat("MasterMute", mute ? -80f : 0f);
            }
        }

        // Getters
        public bool IsMuted => isMuted;
        public float MasterVolume => masterVolume;
        public float SFXVolume => sfxVolume;
        public float VoiceVolume => voiceVolume;
        public float AmbientVolume => ambientVolume;
        public EnvironmentType CurrentEnvironment => currentEnvironment;
        public bool VoiceChatEnabled => enableVoiceChat;
        public int ActiveVoiceChats => voiceChatSources.Count;

        private void OnDestroy()
        {
            // Cleanup audio sources
            if (ambientAudioSource != null)
            {
                ambientAudioSource.Stop();
            }

            foreach (var source in sfxAudioSources)
            {
                if (source != null)
                {
                    source.Stop();
                }
            }

            foreach (var source in voiceAudioSources)
            {
                if (source != null)
                {
                    source.Stop();
                }
            }

            // Cleanup voice chat
            foreach (var kvp in voiceChatSources)
            {
                kvp.Value.audioSource.Stop();
            }
            voiceChatSources.Clear();
        }

        // Enums
        public enum EnvironmentType
        {
            Dungeon,
            Forest,
            Combat,
            Tavern
        }

        public enum SpellType
        {
            Fireball,
            Lightning,
            Healing,
            Shield,
            Teleport
        }

        public enum SpellAudioType
        {
            Cast,
            Hit,
            Miss
        }

        public enum DiceAudioType
        {
            Roll,
            Impact
        }

        public enum SurfaceType
        {
            Stone,
            Dirt,
            Grass,
            Wood,
            Metal
        }

        // Helper classes
        private class VoiceChatSource
        {
            public int playerId;
            public AudioSource audioSource;
            public Vector3 position;
            public bool isActive;
        }
    }
}