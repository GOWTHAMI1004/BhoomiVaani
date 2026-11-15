export interface TimbreSpeechResponse {
  audio_base64: string;
  format: 'audio/wav';
  language: string;
  character: string;
  voice_used: string;
  ai_mode: string;
  duration_estimate_sec: number;
}

export type PlaybackAttempt = 'playing' | 'blocked' | 'failed';

export function parseTimbreSpeechResponse(value: unknown): TimbreSpeechResponse {
  if (!value || typeof value !== 'object') {
    throw new Error('Gnani Timbre returned an invalid response.');
  }
  const response = value as Partial<TimbreSpeechResponse>;
  if (typeof response.audio_base64 !== 'string' || !response.audio_base64.trim()) {
    throw new Error('Gnani Timbre returned no audio data.');
  }
  if (response.format !== 'audio/wav') {
    throw new Error(`Gnani Timbre returned an unsupported audio format${response.format ? `: ${response.format}` : ''}.`);
  }
  if (typeof response.language !== 'string' || typeof response.character !== 'string') {
    throw new Error('Gnani Timbre returned incomplete audio metadata.');
  }
  return response as TimbreSpeechResponse;
}

export function decodeTimbreWav(audioBase64: string, format = 'audio/wav'): Blob {
  if (format !== 'audio/wav') throw new Error(`Unsupported Timbre audio format: ${format}.`);
  let binary: string;
  try {
    binary = atob(audioBase64);
  } catch {
    throw new Error('Gnani Timbre returned invalid base64 audio data.');
  }
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  if (bytes.length < 44 || String.fromCharCode(...bytes.slice(0, 4)) !== 'RIFF'
    || String.fromCharCode(...bytes.slice(8, 12)) !== 'WAVE') {
    throw new Error('Gnani Timbre returned an invalid WAV file.');
  }
  return new Blob([bytes], { type: 'audio/wav' });
}

export async function attemptMediaPlayback(media: Pick<HTMLMediaElement, 'play'>): Promise<PlaybackAttempt> {
  try {
    await media.play();
    return 'playing';
  } catch (error) {
    const name = error instanceof Error ? error.name : '';
    return name === 'NotAllowedError' ? 'blocked' : 'failed';
  }
}
