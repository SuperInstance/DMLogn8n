using UnityEngine;
using Unity.Netcode;
using Photon.Pun;
using Photon.Realtime;
using System.Collections.Generic;
using System.Collections;
using System.Threading.Tasks;
using System.Linq;

namespace DMLog.VR
{
    /// <summary>
    /// Revolutionary Multiplayer VR Room System
    /// Supports cross-platform play, real-time synchronization, and social features
    /// </summary>
    public class MultiplayerVRRoom : NetworkBehaviour, IMatchmakingCallbacks, IInRoomCallbacks
    {
        [Header("Room Configuration")]
        [SerializeField] private string roomName = "DMLog_VR_Room";
        [SerializeField] private int maxPlayers = 8;
        [SerializeField] private bool isPrivate = false;
        [SerializeField] private string roomPassword = "";
        [SerializeField] private RoomType roomType = RoomType.BattleArena;

        [Header("Player Management")]
        [SerializeField] private GameObject playerAvatarPrefab;
        [SerializeField] private Transform[] playerSpawnPoints;
        [SerializeField] private float playerProximityDistance = 2f;

        [Header("Network Settings")]
        [SerializeField] private bool enableVoiceChat = true;
        [SerializeField] private bool enableSpatialVoice = true;
        [SerializeField] private float updateRate = 30f;
        [SerializeField] private float maxNetworkDistance = 100f;

        [Header("Social Features")]
        [SerializeField] private bool enableEmotes = true;
        [SerializeField] private bool enablePlayerInteractions = true;
        [SerializeField] private bool enableSpectatorMode = true;

        // Private state
        private Dictionary<int, NetworkPlayer> networkPlayers = new Dictionary<int, NetworkPlayer>();
        private Dictionary<int, VRPlayerController> playerControllers = new Dictionary<int, VRPlayerController>();
        private Room currentRoom;
        private bool isRoomOwner = false;
        private float lastUpdateTime = 0f;
        private List<int> spectators = new List<int>();

        // Network variables
        private NetworkVariable<RoomState> roomState = new NetworkVariable<RoomState>();
        private NetworkVariable<int> playerCount = new NetworkVariable<int>(0);
        private NetworkVariable<float> roomTime = new NetworkVariable<float>(0f);

        // Events
        public System.Action<Player> OnPlayerJoined;
        public System.Action<Player> OnPlayerLeft;
        public System.Action<RoomState> OnRoomStateChanged;
        public System.Action<string> OnRoomMessage;
        public System.Action<int, Vector3> OnPlayerTeleported;

        public enum RoomType
        {
            BattleArena, SocialHub, CharacterCreator, Custom, Campaign
        }

        public enum RoomState
        {
            Lobby, InSession, Paused, Voting, Ending
        }

        [System.Serializable]
        public class NetworkPlayer
        {
            public int playerId;
            public string playerName;
            public PlayerRole role;
            public bool isReady;
            public bool isSpectating;
            public Vector3 position;
            public Quaternion rotation;
            public Vector3 headPosition;
            public Quaternion headRotation;
            public Vector3 leftHandPosition;
            public Quaternion leftHandRotation;
            public Vector3 rightHandPosition;
            public Quaternion rightHandRotation;
            public string currentEmote;
            public float networkLatency;
        }

        public enum PlayerRole
        {
            Player, DungeonMaster, Spectator, Moderator
        }

        private void Awake()
        {
            InitializeMultiplayerSystem();
        }

        private void Start()
        {
            ConnectToPhoton();
            SetupNetworkCallbacks();
        }

        private void Update()
        {
            if (!IsServer) return;

            UpdateRoomState();
            SyncPlayerData();
            HandlePlayerProximity();
        }

        /// <summary>
        /// Initialize the multiplayer VR room system
        /// </summary>
        private void InitializeMultiplayerSystem()
        {
            Debug.Log("Initializing Multiplayer VR Room System");

            // Initialize Photon settings
            PhotonNetwork.AutomaticallySyncScene = true;
            PhotonNetwork.SendRate = updateRate;
            PhotonNetwork.SerializationRate = updateRate;

            // Set up network callbacks
            PhotonNetwork.AddCallbackTarget(this);

            Debug.Log("Multiplayer VR Room System initialized");
        }

        /// <summary>
        /// Connect to Photon servers
        /// </summary>
        private void ConnectToPhoton()
        {
            if (PhotonNetwork.IsConnected) return;

            Debug.Log("Connecting to Photon...");
            PhotonNetwork.ConnectUsingSettings();
        }

        /// <summary>
        /// Setup network event callbacks
        /// </summary>
        private void SetupNetworkCallbacks()
        {
            PhotonNetwork.AddCallbackTarget(this);
        }

        /// <summary>
        /// Create or join a VR room
        /// </summary>
        public async Task<bool> CreateOrJoinRoom(string customRoomName = null, RoomType type = RoomType.BattleArena)
        {
            if (!PhotonNetwork.IsConnected)
            {
                Debug.LogError("Not connected to Photon");
                return false;
            }

            roomName = customRoomName ?? roomName;
            roomType = type;

            // Try to join existing room first
            var roomOptions = new RoomOptions
            {
                MaxPlayers = maxPlayers,
                IsVisible = !isPrivate,
                IsOpen = true,
                PublishUserId = true,
                CustomRoomProperties = new ExitGames.Client.Photon.Hashtable
                {
                    { "RoomType", roomType.ToString() },
                    { "RoomVersion", "1.0" },
                    { "RequiresPassword", !string.IsNullOrEmpty(roomPassword) }
                }
            };

            // Attempt to join room
            var joinedRoom = PhotonNetwork.JoinOrCreateRoom(roomName, roomOptions, TypedLobby.Default);

            if (joinedRoom)
            {
                Debug.Log($"Successfully joined room: {roomName}");
                isRoomOwner = PhotonNetwork.IsMasterClient;
                await Task.Delay(100); // Allow room to fully load
                return true;
            }
            else
            {
                Debug.LogError($"Failed to join room: {roomName}");
                return false;
            }
        }

        /// <summary>
        /// Leave current room
        /// </summary>
        public void LeaveRoom()
        {
            if (PhotonNetwork.InRoom)
            {
                PhotonNetwork.LeaveRoom();
            }
        }

        /// <summary>
        /// Spawn player avatar in VR space
        /// </summary>
        [ServerRpc]
        public void SpawnPlayerServerRpc(string playerName, PlayerRole role = PlayerRole.Player)
        {
            int playerId = PhotonNetwork.LocalPlayer.ActorNumber;

            // Find available spawn point
            Transform spawnPoint = GetAvailableSpawnPoint();
            if (spawnPoint == null)
            {
                spawnPoint = transform; // Fallback to room center
            }

            // Spawn player avatar
            var playerGO = Instantiate(playerAvatarPrefab, spawnPoint.position, spawnPoint.rotation);
            playerGO.name = $"Player_{playerId}_{playerName}";

            // Add network components
            var networkObject = playerGO.AddComponent<NetworkObject>();
            var playerController = playerGO.AddComponent<VRPlayerController>();
            var networkPlayer = playerGO.AddComponent<NetworkPlayerComponent>();

            // Configure player
            playerController.playerId = playerId;
            playerController.playerName = playerName;
            playerController.playerRole = role;

            // Spawn network object
            networkObject.Spawn();

            // Add to player lists
            var networkPlayerData = new NetworkPlayer
            {
                playerId = playerId,
                playerName = playerName,
                role = role,
                position = spawnPoint.position,
                rotation = spawnPoint.rotation,
                isReady = false,
                isSpectating = role == PlayerRole.Spectator
            };

            networkPlayers[playerId] = networkPlayerData;
            playerControllers[playerId] = playerController;

            // Notify clients
            SpawnPlayerClientRpc(playerId, playerName, (int)role, spawnPoint.position, spawnPoint.rotation);

            Debug.Log($"Spawned player: {playerName} (ID: {playerId})");
        }

        [ClientRpc]
        private void SpawnPlayerClientRpc(int playerId, string playerName, int roleInt, Vector3 position, Quaternion rotation)
        {
            if (IsServer) return; // Skip if we're the server

            PlayerRole role = (PlayerRole)roleInt;

            // Create player avatar for other players
            var playerGO = Instantiate(playerAvatarPrefab, position, rotation);
            playerGO.name = $"Player_{playerId}_{playerName}";

            var playerController = playerGO.AddComponent<VRPlayerController>();
            playerController.playerId = playerId;
            playerController.playerName = playerName;
            playerController.playerRole = role;
            playerController.isNetworkPlayer = true;

            networkPlayers[playerId] = new NetworkPlayer
            {
                playerId = playerId,
                playerName = playerName,
                role = role,
                position = position,
                rotation = rotation,
                isReady = false,
                isSpectating = role == PlayerRole.Spectator
            };

            playerControllers[playerId] = playerController;

            Debug.Log($"Spawned network player: {playerName} (ID: {playerId})");
        }

        /// <summary>
        /// Get available spawn point for new player
        /// </summary>
        private Transform GetAvailableSpawnPoint()
        {
            if (playerSpawnPoints == null || playerSpawnPoints.Length == 0)
                return null;

            // Find first unoccupied spawn point
            foreach (var spawnPoint in playerSpawnPoints)
            {
                bool isOccupied = false;
                foreach (var player in networkPlayers.Values)
                {
                    if (Vector3.Distance(player.position, spawnPoint.position) < playerProximityDistance)
                    {
                        isOccupied = true;
                        break;
                    }
                }

                if (!isOccupied)
                    return spawnPoint;
            }

            // If all points are occupied, return the first one
            return playerSpawnPoints[0];
        }

        /// <summary>
        /// Update room state
        /// </summary>
        private void UpdateRoomState()
        {
            roomTime.Value += Time.deltaTime;

            // Update player count
            playerCount.Value = networkPlayers.Count;

            // Check room state transitions
            switch (roomState.Value)
            {
                case RoomState.Lobby:
                    CheckAllPlayersReady();
                    break;
                case RoomState.InSession:
                    // Handle session logic
                    break;
                case RoomState.Paused:
                    // Handle pause logic
                    break;
            }
        }

        /// <summary>
        /// Synchronize player data across network
        /// </summary>
        private void SyncPlayerData()
        {
            if (Time.time - lastUpdateTime < (1f / updateRate)) return;

            lastUpdateTime = Time.time;

            // Update local player data
            var localPlayer = networkPlayers.GetValueOrDefault(PhotonNetwork.LocalPlayer.ActorNumber);
            if (localPlayer != null && playerControllers.TryGetValue(localPlayer.playerId, out var controller))
            {
                localPlayer.position = controller.transform.position;
                localPlayer.rotation = controller.transform.rotation;
                localPlayer.headPosition = controller.headTransform?.position ?? Vector3.zero;
                localPlayer.headRotation = controller.headTransform?.rotation ?? Quaternion.identity;
                localPlayer.leftHandPosition = controller.leftHandTransform?.position ?? Vector3.zero;
                localPlayer.leftHandRotation = controller.leftHandTransform?.rotation ?? Quaternion.identity;
                localPlayer.rightHandPosition = controller.rightHandTransform?.position ?? Vector3.zero;
                localPlayer.rightHandRotation = controller.rightHandTransform?.rotation ?? Quaternion.identity;

                // Sync to other clients
                UpdatePlayerTransformClientRpc(localPlayer.playerId, localPlayer.position, localPlayer.rotation,
                    localPlayer.headPosition, localPlayer.headRotation,
                    localPlayer.leftHandPosition, localPlayer.leftHandRotation,
                    localPlayer.rightHandPosition, localPlayer.rightHandRotation);
            }
        }

        [ClientRpc]
        private void UpdatePlayerTransformClientRpc(int playerId, Vector3 position, Quaternion rotation,
            Vector3 headPos, Quaternion headRot, Vector3 leftHandPos, Quaternion leftHandRot,
            Vector3 rightHandPos, Quaternion rightHandRot)
        {
            if (IsServer) return;

            if (networkPlayers.TryGetValue(playerId, out var player) &&
                playerControllers.TryGetValue(playerId, out var controller))
            {
                // Update network player transform
                controller.transform.position = position;
                controller.transform.rotation = rotation;

                // Update head and hand transforms
                if (controller.headTransform != null)
                {
                    controller.headTransform.position = headPos;
                    controller.headTransform.rotation = headRot;
                }

                if (controller.leftHandTransform != null)
                {
                    controller.leftHandTransform.position = leftHandPos;
                    controller.leftHandTransform.rotation = leftHandRot;
                }

                if (controller.rightHandTransform != null)
                {
                    controller.rightHandTransform.position = rightHandPos;
                    controller.rightHandTransform.rotation = rightHandRot;
                }

                // Update stored player data
                player.position = position;
                player.rotation = rotation;
                player.headPosition = headPos;
                player.headRotation = headRot;
                player.leftHandPosition = leftHandPos;
                player.leftHandRotation = leftHandRot;
                player.rightHandPosition = rightHandPos;
                player.rightHandRotation = rightHandRot;
            }
        }

        /// <summary>
        /// Handle player proximity interactions
        /// </summary>
        private void HandlePlayerProximity()
        {
            foreach (var player1 in networkPlayers.Values)
            {
                foreach (var player2 in networkPlayers.Values)
                {
                    if (player1.playerId == player2.playerId) continue;

                    float distance = Vector3.Distance(player1.position, player2.position);

                    // Check if players are close enough for interaction
                    if (distance < playerProximityDistance)
                    {
                        OnPlayersProximity(player1.playerId, player2.playerId, true);
                    }
                    else
                    {
                        OnPlayersProximity(player1.playerId, player2.playerId, false);
                    }
                }
            }
        }

        /// <summary>
        /// Handle proximity events between players
        /// </summary>
        private void OnPlayersProximity(int player1Id, int player2Id, bool isNear)
        {
            // Trigger proximity events for social interactions
            if (enablePlayerInteractions && isNear)
            {
                // Could trigger emotes, voice chat changes, etc.
                Debug.Log($"Players {player1Id} and {player2Id} are near each other");
            }
        }

        /// <summary>
        /// Check if all players are ready to start
        /// </summary>
        private void CheckAllPlayersReady()
        {
            if (networkPlayers.Count == 0) return;

            bool allReady = networkPlayers.Values.All(p => p.isReady || p.role == PlayerRole.Spectator);

            if (allReady && networkPlayers.Count > 0)
            {
                StartSession();
            }
        }

        /// <summary>
        /// Start the VR session
        /// </summary>
        [ServerRpc]
        public void StartSessionServerRpc()
        {
            roomState.Value = RoomState.InSession;
            OnRoomStateChanged?.Invoke(RoomState.InSession);
            StartSessionClientRpc();
        }

        [ClientRpc]
        private void StartSessionClientRpc()
        {
            OnRoomStateChanged?.Invoke(RoomState.InSession);
            Debug.Log("VR Session started!");
        }

        /// <summary>
        /// Set player ready status
        /// </summary>
        [ServerRpc]
        public void SetPlayerReadyServerRpc(int playerId, bool isReady)
        {
            if (networkPlayers.TryGetValue(playerId, out var player))
            {
                player.isReady = isReady;
                SetPlayerReadyClientRpc(playerId, isReady);
            }
        }

        [ClientRpc]
        private void SetPlayerReadyClientRpc(int playerId, bool isReady)
        {
            if (networkPlayers.TryGetValue(playerId, out var player))
            {
                player.isReady = isReady;
            }
        }

        /// <summary>
        /// Teleport player to specific location
        /// </summary>
        [ServerRpc]
        public void TeleportPlayerServerRpc(int playerId, Vector3 position)
        {
            if (networkPlayers.TryGetValue(playerId, out var player))
            {
                player.position = position;
                OnPlayerTeleported?.Invoke(playerId, position);
                TeleportPlayerClientRpc(playerId, position);
            }
        }

        [ClientRpc]
        private void TeleportPlayerClientRpc(int playerId, Vector3 position)
        {
            if (playerControllers.TryGetValue(playerId, out var controller))
            {
                controller.transform.position = position;
                OnPlayerTeleported?.Invoke(playerId, position);
            }
        }

        /// <summary>
        /// Send chat message to all players
        /// </summary>
        [ServerRpc]
        public void SendChatMessageServerRpc(string message, int senderId)
        {
            SendChatMessageClientRpc(message, senderId);
        }

        [ClientRpc]
        private void SendChatMessageClientRpc(string message, int senderId)
        {
            OnRoomMessage?.Invoke($"Player {senderId}: {message}");
        }

        /// <summary>
        /// Play emote for player
        /// </summary>
        [ServerRpc]
        public void PlayEmoteServerRpc(int playerId, string emoteName)
        {
            if (enableEmotes && networkPlayers.TryGetValue(playerId, out var player))
            {
                player.currentEmote = emoteName;
                PlayEmoteClientRpc(playerId, emoteName);
            }
        }

        [ClientRpc]
        private void PlayEmoteClientRpc(int playerId, string emoteName)
        {
            if (playerControllers.TryGetValue(playerId, out var controller))
            {
                controller.PlayEmote(emoteName);
            }
        }

        /// <summary>
        /// Switch player to spectator mode
        /// </summary>
        [ServerRpc]
        public void SetSpectatorModeServerRpc(int playerId, bool isSpectator)
        {
            if (networkPlayers.TryGetValue(playerId, out var player))
            {
                player.isSpectating = isSpectator;
                player.role = isSpectator ? PlayerRole.Spectator : PlayerRole.Player;
                SetSpectatorModeClientRpc(playerId, isSpectator);
            }
        }

        [ClientRpc]
        private void SetSpectatorModeClientRpc(int playerId, bool isSpectator)
        {
            if (playerControllers.TryGetValue(playerId, out var controller))
            {
                controller.SetSpectatorMode(isSpectator);
            }
        }

        // Photon Callbacks
        public void OnConnected()
        {
            Debug.Log("Connected to Photon servers");
        }

        public void OnConnectedToMaster()
        {
            Debug.Log("Connected to Photon master server");
        }

        public void OnDisconnected(DisconnectCause cause)
        {
            Debug.LogError($"Disconnected from Photon: {cause}");
        }

        public void OnRegionListReceived(RegionHandler regionHandler)
        {
            Debug.Log("Region list received");
        }

        public void OnRoomListUpdate(List<RoomInfo> roomList)
        {
            // Handle room list updates
        }

        public void OnLobbyStatisticsUpdate(List<TypedLobbyInfo> lobbyStatistics)
        {
            // Handle lobby statistics
        }

        public void OnJoinedLobby()
        {
            Debug.Log("Joined lobby");
        }

        public void OnLeftLobby()
        {
            Debug.Log("Left lobby");
        }

        public void OnRoomPropertiesUpdate(ExitGames.Client.Photon.Hashtable propertiesThatChanged)
        {
            // Handle room property updates
        }

        public void OnPlayerPropertiesUpdate(Player targetPlayer, ExitGames.Client.Photon.Hashtable changedProps)
        {
            // Handle player property updates
        }

        public void OnMasterClientSwitched(Player newMasterClient)
        {
            Debug.Log($"New master client: {newMasterClient.NickName}");
            isRoomOwner = (newMasterClient.ActorNumber == PhotonNetwork.LocalPlayer.ActorNumber);
        }

        public void OnFriendListUpdate(List<FriendInfo> friendList)
        {
            // Handle friend list updates
        }

        public void OnCreatedRoom()
        {
            Debug.Log($"Created room: {roomName}");
            currentRoom = PhotonNetwork.CurrentRoom;
            isRoomOwner = true;

            // Spawn the room owner
            SpawnPlayerServerRpc(PhotonNetwork.LocalPlayer.NickName, PlayerRole.DungeonMaster);
        }

        public void OnCreateRoomFailed(short returnCode, string message)
        {
            Debug.LogError($"Failed to create room: {message}");
        }

        public void OnJoinedRoom()
        {
            Debug.Log($"Joined room: {PhotonNetwork.CurrentRoom.Name}");
            currentRoom = PhotonNetwork.CurrentRoom;

            // Spawn local player
            SpawnPlayerServerRpc(PhotonNetwork.LocalPlayer.NickName, PlayerRole.Player);
        }

        public void OnJoinRoomFailed(short returnCode, string message)
        {
            Debug.LogError($"Failed to join room: {message}");
        }

        public void OnJoinRandomFailed(short returnCode, string message)
        {
            Debug.LogError($"Failed to join random room: {message}");
        }

        public void OnLeftRoom()
        {
            Debug.Log("Left room");
            currentRoom = null;
            isRoomOwner = false;

            // Cleanup players
            networkPlayers.Clear();
            playerControllers.Clear();
        }

        public void OnPlayerEnteredRoom(Player newPlayer)
        {
            Debug.Log($"Player entered room: {newPlayer.NickName}");
            OnPlayerJoined?.Invoke(newPlayer);
        }

        public void OnPlayerLeftRoom(Player otherPlayer)
        {
            Debug.Log($"Player left room: {otherPlayer.NickName}");
            OnPlayerLeft?.Invoke(otherPlayer);

            // Remove player from lists
            int playerId = otherPlayer.ActorNumber;
            networkPlayers.Remove(playerId);

            if (playerControllers.TryGetValue(playerId, out var controller))
            {
                if (controller != null && controller.gameObject != null)
                {
                    Destroy(controller.gameObject);
                }
                playerControllers.Remove(playerId);
            }
        }

        private void OnDestroy()
        {
            // Cleanup Photon callbacks
            PhotonNetwork.RemoveCallbackTarget(this);

            // Leave room if still connected
            if (PhotonNetwork.InRoom)
            {
                PhotonNetwork.LeaveRoom();
            }
        }
    }

    /// <summary>
    /// Network player component for synchronizing player data
    /// </summary>
    public class NetworkPlayerComponent : NetworkBehaviour
    {
        public NetworkVariable<Vector3> networkPosition = new NetworkVariable<Vector3>();
        public NetworkVariable<Quaternion> networkRotation = new NetworkVariable<Quaternion>();
        public NetworkVariable<string> playerName = new NetworkVariable<string>();

        private void Update()
        {
            if (IsOwner)
            {
                networkPosition.Value = transform.position;
                networkRotation.Value = transform.rotation;
            }
            else
            {
                transform.position = networkPosition.Value;
                transform.rotation = networkRotation.Value;
            }
        }
    }
}