import test from 'node:test';
import assert from 'node:assert/strict';
import { attemptMediaPlayback, decodeTimbreWav, parseTimbreSpeechResponse } from '../src/services/timbreAudio.ts';

function wavBase64(): string {
  const bytes = new Uint8Array(46);
  bytes.set(new TextEncoder().encode('RIFF'), 0);
  bytes.set(new TextEncoder().encode('WAVE'), 8);
  bytes.set(new TextEncoder().encode('fmt '), 12);
  bytes.set(new TextEncoder().encode('data'), 36);
  return btoa(String.fromCharCode(...bytes));
}

test('decodes the documented base64 WAV response as audio/wav', async () => {
  const blob = decodeTimbreWav(wavBase64(), 'audio/wav');
  assert.equal(blob.type, 'audio/wav');
  assert.equal(blob.size, 46);
  assert.equal(new TextDecoder().decode(await blob.slice(0, 4).arrayBuffer()), 'RIFF');
});

test('parses the JSON SpeakResponse schema and rejects missing or wrong-format audio', () => {
  const parsed = parseTimbreSpeechResponse({
    audio_base64: wavBase64(), format: 'audio/wav', language: 'te', character: 'bhoomi',
    voice_used: 'Bhoomi cloned voice', ai_mode: 'GNANI_TIMBRE_VOICE_CLONE', duration_estimate_sec: 1,
  });
  assert.equal(parsed.format, 'audio/wav');
  assert.equal(parsed.language, 'te');
  assert.throws(() => parseTimbreSpeechResponse({ format: 'audio/wav' }), /no audio data/);
  assert.throws(() => parseTimbreSpeechResponse({ ...parsed, format: 'audio/mpeg' }), /unsupported audio format/);
});

test('reports playback success, browser autoplay blocking and media failure', async () => {
  assert.equal(await attemptMediaPlayback({ play: async () => undefined }), 'playing');
  const blocked = Object.assign(new Error('blocked'), { name: 'NotAllowedError' });
  assert.equal(await attemptMediaPlayback({ play: async () => { throw blocked; } }), 'blocked');
  assert.equal(await attemptMediaPlayback({ play: async () => { throw new Error('decode'); } }), 'failed');
});

test('uses the same playback-state handler for a generated video element', async () => {
  let starts = 0;
  const generatedVideo = { play: async () => { starts += 1; } };
  assert.equal(await attemptMediaPlayback(generatedVideo), 'playing');
  assert.equal(starts, 1);
});
