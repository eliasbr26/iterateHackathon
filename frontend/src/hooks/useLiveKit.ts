import { useState, useEffect, useCallback } from 'react';
import { Room, RoomEvent, Track, RemoteTrackPublication, RemoteParticipant } from 'livekit-client';

interface LiveKitConfig {
  url: string;
  token: string;
}

export const useLiveKit = () => {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);

  const connect = useCallback(async (config: LiveKitConfig) => {
    if (room) {
      console.warn('Already connected to a room');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Setup event listeners
      newRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log('Track subscribed:', track.kind, 'from', participant.identity);
      });

      newRoom.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
        console.log('Track unsubscribed:', track.kind, 'from', participant.identity);
      });

      newRoom.on(RoomEvent.ParticipantConnected, (participant) => {
        console.log('Participant connected:', participant.identity);
      });

      newRoom.on(RoomEvent.ParticipantDisconnected, (participant) => {
        console.log('Participant disconnected:', participant.identity);
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        console.log('Disconnected from room');
        setIsConnected(false);
      });

      // Connect to room
      await newRoom.connect(config.url, config.token);
      console.log('Connected to room:', newRoom.name);

      // Enable camera and microphone
      await newRoom.localParticipant.enableCameraAndMicrophone();

      setRoom(newRoom);
      setIsConnected(true);
    } catch (err) {
      console.error('Failed to connect to room:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setIsConnecting(false);
    }
  }, [room]);

  const disconnect = useCallback(async () => {
    if (room) {
      await room.disconnect();
      setRoom(null);
      setIsConnected(false);
    }
  }, [room]);

  const toggleAudio = useCallback(async () => {
    if (room) {
      const enabled = !audioEnabled;
      await room.localParticipant.setMicrophoneEnabled(enabled);
      setAudioEnabled(enabled);
    }
  }, [room, audioEnabled]);

  const toggleVideo = useCallback(async () => {
    if (room) {
      const enabled = !videoEnabled;
      await room.localParticipant.setCameraEnabled(enabled);
      setVideoEnabled(enabled);
    }
  }, [room, videoEnabled]);

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  return {
    room,
    isConnected,
    isConnecting,
    error,
    audioEnabled,
    videoEnabled,
    connect,
    disconnect,
    toggleAudio,
    toggleVideo,
  };
};
