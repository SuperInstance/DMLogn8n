/**
 * WebRTC Manager - Handles peer-to-peer voice connections and SFU integration
 * Provides low-latency audio streaming with automatic echo cancellation and noise suppression
 */

import { io } from 'socket.io-client';
import { Device } from 'mediasoup-client';

export class WebRTCManager {
  constructor(config) {
    this.config = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ],
      maxLatency: 50, // ms
      enableSFU: true,
      enableP2P: true,
      ...config
    };

    // Connection management
    this.connections = new Map();
    this.localStream = null;
    this.socket = null;
    this.device = null;
    this.producer = null;
    this.consumers = new Map();

    // Room information
    this.roomId = null;
    this.participantId = null;
    this.participants = new Map();

    // SFU (Selective Forwarding Unit) setup
    this.sfuConfig = {
      routerRtpCapabilities: null,
      transport: null,
      recvTransport: null,
      sendTransport: null
    };

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      latency: 0,
      packetLoss: 0,
      bandwidth: 0,
      connectionQuality: 1.0
    };

    // Connection state
    this.state = {
      isConnected: false,
      isProducing: false,
      isReceiving: false
    };
  }

  /**
   * Connect to a voice chat room
   */
  async connect(roomId, serverConfig) {
    try {
      this.roomId = roomId;
      this.emit('connecting', { roomId });

      // Initialize socket connection
      this.socket = io(serverConfig.url, {
        query: { roomId },
        transports: ['websocket']
      });

      // Set up socket event handlers
      this.setupSocketHandlers();

      // Initialize SFU if enabled
      if (this.config.enableSFU) {
        await this.initializeSFU();
      }

      this.state.isConnected = true;
      this.emit('connected', { roomId });

    } catch (error) {
      console.error('Failed to connect to room:', error);
      this.emit('connectionError', error);
      throw error;
    }
  }

  /**
   * Initialize SFU (Selective Forwarding Unit) for group calls
   */
  async initializeSFU() {
    try {
      // Create mediasoup device
      this.device = new Device();

      // Request router RTP capabilities
      const data = await this.request('getRouterRtpCapabilities');
      await this.device.load({ routerRtpCapabilities: data.rtpCapabilities });

      // Create send transport
      if (this.device.canProduce('audio')) {
        const sendTransportData = await this.request('createWebRtcTransport', {
          forceTcp: false,
          producing: true,
          consuming: false,
          sctpCapabilities: undefined
        });

        this.sfuConfig.sendTransport = this.device.createSendTransport({
          id: sendTransportData.id,
          iceParameters: sendTransportData.iceParameters,
          iceCandidates: sendTransportData.iceCandidates,
          dtlsParameters: sendTransportData.dtlsParameters,
          sctpParameters: sendTransportData.sctpParameters,
          iceServers: this.config.iceServers,
          proprietaryConstraints: {
            optional: [{ googDscp: true }]
          }
        });

        this.setupSendTransportHandlers();
      }

      // Create receive transport
      const recvTransportData = await this.request('createWebRtcTransport', {
        forceTcp: false,
        producing: false,
        consuming: true,
        sctpCapabilities: undefined
      });

      this.sfuConfig.recvTransport = this.device.createRecvTransport({
        id: recvTransportData.id,
        iceParameters: recvTransportData.iceParameters,
        iceCandidates: recvTransportData.iceCandidates,
        dtlsParameters: recvTransportData.dtlsParameters,
        sctpParameters: recvTransportData.sctpParameters,
        iceServers: this.config.iceServers
      });

      this.setupReceiveTransportHandlers();

    } catch (error) {
      console.error('Failed to initialize SFU:', error);
      throw error;
    }
  }

  /**
   * Set up send transport event handlers
   */
  setupSendTransportHandlers() {
    this.sfuConfig.sendTransport.on('connect', async ({ dtlsParameters }, callback, errback) => {
      try {
        await this.request('connectWebRtcTransport', {
          transportId: this.sfuConfig.sendTransport.id,
          dtlsParameters
        });
        callback();
      } catch (error) {
        errback(error);
      }
    });

    this.sfuConfig.sendTransport.on('produce', async ({ kind, rtpParameters, appData }, callback, errback) => {
      try {
        const { id } = await this.request('produce', {
          transportId: this.sfuConfig.sendTransport.id,
          kind,
          rtpParameters,
          appData
        });
        callback({ id });
      } catch (error) {
        errback(error);
      }
    });

    this.sfuConfig.sendTransport.on('connectionstatechange', (connectionState) => {
      this.emit('transportConnectionStateChange', {
        type: 'send',
        connectionState
      });
    });
  }

  /**
   * Set up receive transport event handlers
   */
  setupReceiveTransportHandlers() {
    this.sfuConfig.recvTransport.on('connect', async ({ dtlsParameters }, callback, errback) => {
      try {
        await this.request('connectWebRtcTransport', {
          transportId: this.sfuConfig.recvTransport.id,
          dtlsParameters
        });
        callback();
      } catch (error) {
        errback(error);
      }
    });

    this.sfuConfig.recvTransport.on('connectionstatechange', (connectionState) => {
      this.emit('transportConnectionStateChange', {
        type: 'receive',
        connectionState
      });
    });
  }

  /**
   * Set up socket event handlers
   */
  setupSocketHandlers() {
    this.socket.on('connect', () => {
      this.emit('socketConnected');
    });

    this.socket.on('disconnect', () => {
      this.emit('socketDisconnected');
    });

    this.socket.on('newProducer', async (data) => {
      await this.handleNewProducer(data);
    });

    this.socket.on('producerClosed', (data) => {
      this.handleProducerClosed(data);
    });

    this.socket.on('participantJoined', (data) => {
      this.handleParticipantJoined(data);
    });

    this.socket.on('participantLeft', (data) => {
      this.handleParticipantLeft(data);
    });

    this.socket.on('activeSpeakers', (data) => {
      this.handleActiveSpeakers(data);
    });
  }

  /**
   * Add local media stream
   */
  async addLocalStream(stream) {
    try {
      this.localStream = stream;

      if (this.config.enableSFU && this.sfuConfig.sendTransport) {
        // Create producer for SFU
        const audioTrack = stream.getAudioTracks()[0];
        if (audioTrack) {
          this.producer = await this.sfuConfig.sendTransport.produce({
            track: audioTrack,
            codecOptions: {
              opusStereo: true,
              opusDtx: true,
              opusFec: true,
              opusPtime: 20,
              opusMaxAverageBitrate: 128000
            }
          });

          this.state.isProducing = true;
          this.emit('producerCreated', { producerId: this.producer.id });
        }
      }

      // Also set up P2P connections if enabled
      if (this.config.enableP2P) {
        await this.setupP2PConnections();
      }

    } catch (error) {
      console.error('Failed to add local stream:', error);
      throw error;
    }
  }

  /**
   * Set up peer-to-peer connections
   */
  async setupP2PConnections() {
    for (const [participantId, participant] of this.participants) {
      if (participantId !== this.participantId && !this.connections.has(participantId)) {
        await this.createPeerConnection(participantId, participant);
      }
    }
  }

  /**
   * Create peer connection with another participant
   */
  async createPeerConnection(participantId, participant) {
    try {
      const configuration = {
        iceServers: this.config.iceServers,
        iceCandidatePoolSize: 10,
        bundlePolicy: 'max-bundle',
        rtcpMuxPolicy: 'require'
      };

      const peerConnection = new RTCPeerConnection(configuration);
      const connection = {
        pc: peerConnection,
        participantId,
        isInitiator: participant.isInitiator || false,
        streams: new Map()
      };

      // Set up event handlers
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit('iceCandidate', {
            candidate: event.candidate,
            participantId: this.participantId,
            targetParticipantId: participantId
          });
        }
      };

      peerConnection.ontrack = (event) => {
        this.handleRemoteTrack(participantId, event.streams[0]);
      };

      peerConnection.onconnectionstatechange = () => {
        this.emit('peerConnectionStateChange', {
          participantId,
          connectionState: peerConnection.connectionState
        });
      };

      peerConnection.oniceconnectionstatechange = () => {
        this.emit('iceConnectionStateChange', {
          participantId,
          iceConnectionState: peerConnection.iceConnectionState
        });
      };

      // Add local stream
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => {
          peerConnection.addTrack(track, this.localStream);
        });
      }

      this.connections.set(participantId, connection);

      // Start connection negotiation
      if (connection.isInitiator) {
        await this.createOffer(participantId);
      }

    } catch (error) {
      console.error('Failed to create peer connection:', error);
      throw error;
    }
  }

  /**
   * Create WebRTC offer
   */
  async createOffer(participantId) {
    try {
      const connection = this.connections.get(participantId);
      if (!connection) return;

      const offer = await connection.pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      });

      await connection.pc.setLocalDescription(offer);

      this.socket.emit('offer', {
        offer,
        participantId: this.participantId,
        targetParticipantId: participantId
      });

    } catch (error) {
      console.error('Failed to create offer:', error);
    }
  }

  /**
   * Handle incoming WebRTC offer
   */
  async handleOffer(data) {
    try {
      const { offer, participantId, targetParticipantId } = data;

      if (targetParticipantId !== this.participantId) return;

      let connection = this.connections.get(participantId);
      if (!connection) {
        await this.createPeerConnection(participantId, { isInitiator: false });
        connection = this.connections.get(participantId);
      }

      await connection.pc.setRemoteDescription(offer);
      const answer = await connection.pc.createAnswer();
      await connection.pc.setLocalDescription(answer);

      this.socket.emit('answer', {
        answer,
        participantId: this.participantId,
        targetParticipantId: participantId
      });

    } catch (error) {
      console.error('Failed to handle offer:', error);
    }
  }

  /**
   * Handle incoming WebRTC answer
   */
  async handleAnswer(data) {
    try {
      const { answer, participantId, targetParticipantId } = data;

      if (targetParticipantId !== this.participantId) return;

      const connection = this.connections.get(participantId);
      if (connection) {
        await connection.pc.setRemoteDescription(answer);
      }

    } catch (error) {
      console.error('Failed to handle answer:', error);
    }
  }

  /**
   * Handle ICE candidate
   */
  async handleIceCandidate(data) {
    try {
      const { candidate, participantId, targetParticipantId } = data;

      if (targetParticipantId !== this.participantId) return;

      const connection = this.connections.get(participantId);
      if (connection) {
        await connection.pc.addIceCandidate(candidate);
      }

    } catch (error) {
      console.error('Failed to handle ICE candidate:', error);
    }
  }

  /**
   * Handle new producer from SFU
   */
  async handleNewProducer(data) {
    try {
      const { producerId, participantId } = data;

      if (this.consumers.has(producerId)) return;

      await this.consume(producerId, participantId);

    } catch (error) {
      console.error('Failed to handle new producer:', error);
    }
  }

  /**
   * Consume audio from SFU
   */
  async consume(producerId, participantId) {
    try {
      const consumerData = await this.request('consume', {
        rtpCapabilities: this.device.rtpCapabilities,
        producerId,
        transportId: this.sfuConfig.recvTransport.id
      });

      const consumer = await this.sfuConfig.recvTransport.consume({
        id: consumerData.id,
        producerId,
        kind: consumerData.kind,
        rtpParameters: consumerData.rtpParameters
      });

      this.consumers.set(producerId, {
        consumer,
        participantId
      });

      // Handle stream
      const { track } = consumer;
      const stream = new MediaStream([track]);
      this.handleRemoteTrack(participantId, stream);

      // Resume consumer
      await this.request('resumeConsumer', { consumerId: consumer.id });

      this.emit('consumerCreated', { producerId, participantId, consumer });

    } catch (error) {
      console.error('Failed to consume:', error);
    }
  }

  /**
   * Handle remote track
   */
  handleRemoteTrack(participantId, stream) {
    this.emit('streamAdded', {
      participantId,
      stream
    });
  }

  /**
   * Handle producer closed
   */
  handleProducerClosed(data) {
    const { producerId } = data;

    if (this.consumers.has(producerId)) {
      const consumerInfo = this.consumers.get(producerId);
      consumerInfo.consumer.close();
      this.consumers.delete(producerId);

      this.emit('streamRemoved', {
        participantId: consumerInfo.participantId
      });
    }
  }

  /**
   * Handle participant joined
   */
  handleParticipantJoined(data) {
    const { participant } = data;
    this.participants.set(participant.id, participant);

    if (this.config.enableP2P) {
      this.setupP2PConnections();
    }

    this.emit('participantJoined', participant);
  }

  /**
   * Handle participant left
   */
  handleParticipantLeft(data) {
    const { participantId } = data;

    // Clean up peer connection
    if (this.connections.has(participantId)) {
      const connection = this.connections.get(participantId);
      connection.pc.close();
      this.connections.delete(participantId);
    }

    this.participants.delete(participantId);

    this.emit('participantLeft', { participantId });
  }

  /**
   * Handle active speakers
   */
  handleActiveSpeakers(data) {
    this.emit('activeSpeakers', data);
  }

  /**
   * Request helper for socket communication
   */
  request(method, data = {}) {
    return new Promise((resolve, reject) => {
      this.socket.emit(method, data, (response) => {
        if (response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response);
        }
      });
    });
  }

  /**
   * Get connection statistics
   */
  async getStats() {
    const stats = {
      connections: this.connections.size,
      consumers: this.consumers.size,
      sfuConnected: !!this.sfuConfig.sendTransport
    };

    // Get peer connection stats
    for (const [participantId, connection] of this.connections) {
      try {
        const pcStats = await connection.pc.getStats();
        stats[participantId] = this.parseStats(pcStats);
      } catch (error) {
        console.warn(`Failed to get stats for ${participantId}:`, error);
      }
    }

    // Get SFU stats
    if (this.producer) {
      try {
        const producerStats = await this.producer.getStats();
        stats.producer = this.parseProducerStats(producerStats);
      } catch (error) {
        console.warn('Failed to get producer stats:', error);
      }
    }

    return stats;
  }

  /**
   * Parse WebRTC statistics
   */
  parseStats(statsReport) {
    const stats = {
      bandwidth: 0,
      packetsLost: 0,
      packetsReceived: 0,
      roundTripTime: 0,
      jitter: 0
    };

    statsReport.forEach(report => {
      switch (report.type) {
        case 'inbound-rtp':
          stats.packetsReceived = report.packetsReceived || 0;
          stats.packetsLost = report.packetsLost || 0;
          stats.jitter = report.jitter || 0;
          break;
        case 'outbound-rtp':
          stats.bandwidth = report.bitrate || 0;
          break;
        case 'remote-candidate':
          stats.roundTripTime = report.roundTripTime || 0;
          break;
      }
    });

    return stats;
  }

  /**
   * Parse producer statistics
   */
  parseProducerStats(statsReport) {
    return {
      bitrate: statsReport.bitrate || 0,
      packetsSent: statsReport.packetsSent || 0,
      packetsLost: statsReport.packetsLost || 0,
      rtt: statsReport.rtt || 0
    };
  }

  /**
   * Get connection count
   */
  getConnectionCount() {
    return this.connections.size;
  }

  /**
   * Event emitter methods
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebRTC event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Disconnect from the room
   */
  async disconnect() {
    try {
      // Close producer
      if (this.producer) {
        this.producer.close();
        this.producer = null;
      }

      // Close consumers
      for (const [producerId, consumerInfo] of this.consumers) {
        consumerInfo.consumer.close();
      }
      this.consumers.clear();

      // Close transports
      if (this.sfuConfig.sendTransport) {
        this.sfuConfig.sendTransport.close();
      }
      if (this.sfuConfig.recvTransport) {
        this.sfuConfig.recvTransport.close();
      }

      // Close peer connections
      for (const [participantId, connection] of this.connections) {
        connection.pc.close();
      }
      this.connections.clear();

      // Close socket
      if (this.socket) {
        this.socket.disconnect();
      }

      // Reset state
      this.state.isConnected = false;
      this.state.isProducing = false;
      this.state.isReceiving = false;

      this.emit('disconnected');

    } catch (error) {
      console.error('Error during disconnect:', error);
    }
  }

  /**
   * Mute/unmute local audio
   */
  muteLocalAudio(mute = true) {
    if (this.localStream) {
      this.localStream.getAudioTracks().forEach(track => {
        track.enabled = !mute;
      });
    }

    if (this.producer) {
      this.producer.pause();
    }

    this.emit('localAudioMuted', { muted: mute });
  }

  /**
   * Unmute local audio
   */
  unmuteLocalAudio() {
    this.muteLocalAudio(false);
  }

  /**
   * Check if local audio is muted
   */
  isLocalAudioMuted() {
    if (this.localStream) {
      const audioTrack = this.localStream.getAudioTracks()[0];
      return audioTrack ? !audioTrack.enabled : true;
    }
    return true;
  }
}