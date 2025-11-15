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

    const handleTrackSubscribed = (track: any) => {
      if (track.kind === Track.Kind.Video) {
        track.attach(videoElement);
      } else if (track.kind === Track.Kind.Audio && !isLocal) {
        track.attach(audioElement);
      }
    };

    const handleTrackUnsubscribed = (track: any) => {
      track.detach();
    };

    // Attach existing tracks
    participant.videoTrackPublications.forEach((publication) => {
      if (publication.track) {
        handleTrackSubscribed(publication.track);
      }
    });

    participant.audioTrackPublications.forEach((publication) => {
      if (publication.track && !isLocal) {
        handleTrackSubscribed(publication.track);
      }
    });

    // Listen for new tracks
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
