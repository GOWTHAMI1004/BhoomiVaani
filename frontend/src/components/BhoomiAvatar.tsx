import React, { useEffect, useState } from 'react';
import { CharacterState } from '../types';

interface BhoomiAvatarProps {
  state: CharacterState;
  audioLevel: number;
  speakingVideoUrl: string;
  videoRef: React.RefObject<HTMLVideoElement>;
  onVideoError: () => void;
}

export const BHOOMI_SPEAKING_VIDEO_URL = '/assets/bhoomivaani-avatar.mp4';
const AVATAR_POSTER = '/assets/bhoomivaani-avatar.png';

export const BhoomiAvatar: React.FC<BhoomiAvatarProps> = ({
  state, audioLevel, speakingVideoUrl, videoRef, onVideoError,
}) => {
  const [videoFailed, setVideoFailed] = useState(false);
  const [videoEnded, setVideoEnded] = useState(false);
  const videoSource = speakingVideoUrl || BHOOMI_SPEAKING_VIDEO_URL;
  const stateName = ({ idle: 'Ready', listening: 'Listening', thinking: 'Thinking', speaking: 'Speaking' } as const)[state];
  const level = Math.min(Math.max(audioLevel, 0), 0.65);

  useEffect(() => {
    setVideoFailed(false);
    setVideoEnded(false);
  }, [videoSource]);

  return (
    <div className={`bhoomi-avatar-media avatar-state-${state}`}>
      <img className="bhoomi-avatar-poster-fallback" src={AVATAR_POSTER} alt="Bhoomi" />
      <video
        key={videoSource}
        ref={videoRef}
        className={`bhoomi-avatar-video${state === 'speaking' && !videoFailed && !videoEnded ? ' is-speaking' : ''}`}
        src={videoSource}
        autoPlay={false}
        muted
        playsInline
        controls={false}
        loop={false}
        preload="none"
        onError={() => { setVideoFailed(true); onVideoError(); }}
        onEnded={() => { setVideoEnded(true); videoRef.current?.pause(); }}
      />
      <span className="bhoomi-avatar-state" aria-live="polite">{stateName}</span>
      {state === 'speaking' && (
        <span className="bhoomi-audio-meter" aria-label="Bhoomi’s generated audio is playing">
          {[0.55, 0.85, 0.65, 1, 0.72].map((weight, index) => (
            <i key={index} style={{ transform: `scaleY(${0.18 + level * weight * 2.2})` }} />
          ))}
        </span>
      )}
    </div>
  );
};
