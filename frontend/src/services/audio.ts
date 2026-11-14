export function encodeAudioBufferAsWav(buffer: AudioBuffer): { blob: Blob; rms: number } {
  const channelCount = buffer.numberOfChannels;
  const samples = new Float32Array(buffer.length);
  let squareSum = 0;
  for (let i = 0; i < buffer.length; i += 1) {
    let sample = 0;
    for (let channel = 0; channel < channelCount; channel += 1) {
      sample += buffer.getChannelData(channel)[i] / channelCount;
    }
    samples[i] = sample;
    squareSum += sample * sample;
  }

  const dataLength = samples.length * 2;
  const bytes = new ArrayBuffer(44 + dataLength);
  const view = new DataView(bytes);
  const writeText = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i += 1) view.setUint8(offset + i, value.charCodeAt(i));
  };
  writeText(0, 'RIFF');
  view.setUint32(4, 36 + dataLength, true);
  writeText(8, 'WAVE');
  writeText(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, buffer.sampleRate, true);
  view.setUint32(28, buffer.sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeText(36, 'data');
  view.setUint32(40, dataLength, true);
  for (let i = 0; i < samples.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }
  return {
    blob: new Blob([bytes], { type: 'audio/wav' }),
    rms: Math.sqrt(squareSum / Math.max(samples.length, 1)),
  };
}
