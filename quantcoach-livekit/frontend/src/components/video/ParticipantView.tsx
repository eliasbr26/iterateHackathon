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

    const attachTrack = (track: any) => {
      if (track.kind === Track.Kind.Video) {
        track.attach(videoElement);
      } else if (track.kind === Track.Kind.Audio && !isLocal) {
        track.attach(audioElement);
      }
    };

    const detachTrack = (track: any) => {
      track.detach();
    };

    // Handle track subscribed (for remote participants)
    const handleTrackSubscribed = (track: any) => {
      attachTrack(track);
    };

    const handleTrackUnsubscribed = (track: any) => {
      detachTrack(track);
    };

    // Attach existing tracks
    participant.videoTrackPublications.forEach((publication) => {
      if (publication.track && publication.isSubscribed) {
        attachTrack(publication.track);
      }
    });

    participant.audioTrackPublications.forEach((publication) => {
      if (publication.track && publication.isSubscribed && !isLocal) {
        attachTrack(publication.track);
      }
    });

    // Listen for track subscription events (remote participants)
    participant.on('trackSubscribed', handleTrackSubscribed);
    participant.on('trackUnsubscribed', handleTrackUnsubscribed);

    return () => {
      participant.off('trackSubscribed', handleTrackSubscribed);
      participant.off('trackUnsubscribed', handleTrackUnsubscribed);

      // Detach all tracks on cleanup
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
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocal}
        className="w-full h-full object-cover"
      />
      <audio ref={audioRef} autoPlay />
      <div className="absolute bottom-2 left-2 bg-black/70 text-white px-3 py-1 rounded text-sm">
        {isLocal ? 'You' : participant.identity}
      </div>
    </div>
  );
};
