import { useEffect, useRef } from 'react';
import { Participant, Track } from 'livekit-client';

interface ParticipantViewProps {
  participant: Participant;
  isLocal?: boolean;
}

export const ParticipantView = ({ participant, isLocal = false }: ParticipantViewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const videoElement = videoRef.current;
    const audioElement = audioRef.current;

    if (!videoElement || !audioElement) return;

    console.log('ParticipantView: Setting up tracks for', participant.identity, {
      isLocal,
      videoTracks: participant.videoTrackPublications.size,
      audioTracks: participant.audioTrackPublications.size
    });

    const attachTrack = (track: any) => {
      if (track.kind === Track.Kind.Video) {
        console.log('ParticipantView: Attaching video track for', participant.identity);
        track.attach(videoElement);
      } else if (track.kind === Track.Kind.Audio && !isLocal) {
        console.log('ParticipantView: Attaching audio track for', participant.identity);
        track.attach(audioElement);
      }
    };

    const detachTrack = (track: any) => {
      track.detach();
    };

    // Handle track subscribed (for remote participants)
    const handleTrackSubscribed = (track: any) => {
      console.log('ParticipantView: Track subscribed', track.kind, 'for', participant.identity);
      attachTrack(track);
    };

    const handleTrackUnsubscribed = (track: any) => {
      console.log('ParticipantView: Track unsubscribed', track.kind, 'for', participant.identity);
      detachTrack(track);
    };

    // Attach existing tracks
    // For local participants, tracks are published, not subscribed
    // For remote participants, check isSubscribed
    participant.videoTrackPublications.forEach((publication) => {
      console.log('ParticipantView: Video publication found', {
        participant: participant.identity,
        isLocal,
        hasTrack: !!publication.track,
        isSubscribed: publication.isSubscribed,
        trackSid: publication.trackSid,
        source: publication.source
      });
      if (publication.track) {
        if (isLocal || publication.isSubscribed) {
          attachTrack(publication.track);
        } else {
          console.log('ParticipantView: Skipping video track - not subscribed');
        }
      } else {
        console.log('ParticipantView: No track available yet');
      }
    });

    participant.audioTrackPublications.forEach((publication) => {
      if (publication.track && !isLocal) {
        if (publication.isSubscribed) {
          attachTrack(publication.track);
        }
      }
    });

    // Listen for track subscription events (remote participants)
    participant.on('trackSubscribed', handleTrackSubscribed);
    participant.on('trackUnsubscribed', handleTrackUnsubscribed);

    return () => {
      participant.off('trackSubscribed', handleTrackSubscribed);
      participant.off('trackUnsubscribed', handleTrackUnsubscribed);

      // Detach all tracks
      participant.videoTrackPublications.forEach((publication) => {
        if (publication.track) {
          publication.track.detach();
        }
      });

      participant.audioTrackPublications.forEach((publication) => {
        if (publication.track) {
          publication.track.detach();
        }
      });
    };
  }, [participant, isLocal]);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        backgroundColor: '#000',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocal}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          backgroundColor: '#000',
        }}
      />
      <audio ref={audioRef} autoPlay />
      <div
        style={{
          position: 'absolute',
          bottom: '8px',
          left: '8px',
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '4px 12px',
          borderRadius: '4px',
          fontSize: '14px',
          zIndex: 10,
        }}
      >
        {isLocal ? 'You' : participant.identity}
      </div>
    </div>
  );
};
