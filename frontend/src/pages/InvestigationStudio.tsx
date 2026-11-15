import React, { FormEvent, useEffect, useRef, useState } from 'react';
import { AlertCircle, ArrowUp, ChevronDown, Download, FileUp, Mic, MicOff, RotateCcw, Volume2, VolumeX } from 'lucide-react';
import { api } from '../services/api';
import { encodeAudioBufferAsWav } from '../services/audio';
import { createManagedObjectUrl } from '../services/avatarMedia';
import { attemptMediaPlayback, decodeTimbreWav } from '../services/timbreAudio';
import { BHOOMI_SPEAKING_VIDEO_URL, BhoomiAvatar } from '../components/BhoomiAvatar';
import {
  CharacterSpeechItem,
  CharacterState,
  ConversationLanguage,
  DocumentAnalysisResponse,
  InvestigationReport,
} from '../types';

type ConversationEntry = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  speech?: CharacterSpeechItem & { lipSyncVideo?: Blob; lipSyncError?: string };
  report?: InvestigationReport | null;
  document?: DocumentAnalysisResponse;
};

const GREETING: ConversationEntry = {
  id: 'welcome',
  role: 'assistant',
  text: "Hello! I'm Bhoomi. Are you planning to buy land?",
};

const SUPPORTED_LANGUAGES: ConversationLanguage[] = ['en', 'te', 'hi', 'ta', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa'];

const SCRIPT_LANGUAGES: Array<{ pattern: RegExp; language: ConversationLanguage }> = [
  { pattern: /[\u0c00-\u0c7f]/u, language: 'te' },
  { pattern: /[\u0900-\u097f]/u, language: 'hi' },
  { pattern: /[\u0b80-\u0bff]/u, language: 'ta' },
  { pattern: /[\u0c80-\u0cff]/u, language: 'kn' },
  { pattern: /[\u0d00-\u0d7f]/u, language: 'ml' },
  { pattern: /[\u0980-\u09ff]/u, language: 'bn' },
  { pattern: /[\u0a80-\u0aff]/u, language: 'gu' },
  { pattern: /[\u0a00-\u0a7f]/u, language: 'pa' },
];

function detectTypedLanguage(text: string): ConversationLanguage {
  return SCRIPT_LANGUAGES.find(({ pattern }) => pattern.test(text))?.language ?? 'en';
}

function getDetectedLanguage(code: string | undefined): ConversationLanguage | undefined {
  const normalized = code?.split(/[-_]/u)[0]?.trim().toLowerCase();
  return SUPPORTED_LANGUAGES.find((language) => language === normalized);
}

function getBhoomiReply(items: CharacterSpeechItem[]): CharacterSpeechItem {
  const reply = [...items].reverse().find((item) => item.character === 'bhoomi');
  if (!reply?.text.trim()) throw new Error('Bhoomi did not return a response. Please try again.');
  return reply;
}

function getLanguageName(language: ConversationLanguage): string {
  return ({
    en: 'English',
    te: 'Telugu',
    hi: 'Hindi',
    ta: 'Tamil',
    kn: 'Kannada',
    ml: 'Malayalam',
    mr: 'Marathi',
    bn: 'Bengali',
    gu: 'Gujarati',
    pa: 'Punjabi',
  })[language];
}

function getEvidenceStatusLabel(status: string): string {
  return ({
    VERIFIED: 'Verified',
    CONTRADICTED: 'Contradicted',
    UNVERIFIED: 'Unverified',
    MISSING_INFORMATION: 'Missing information',
  })[status] ?? status.replace(/_/g, ' ').toLowerCase();
}

function getAvatarState(phase: string): CharacterState {
  if (phase === 'listening') return 'listening';
  if (phase === 'thinking' || phase === 'transcribing') return 'thinking';
  if (phase === 'speaking') return 'speaking';
  return 'idle';
}

function newMessageId(role: 'user' | 'assistant'): string {
  return `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const InvestigationStudio: React.FC = () => {
  const [messages, setMessages] = useState<ConversationEntry[]>([GREETING]);
  const [question, setQuestion] = useState('');
  const [phase, setPhase] = useState<'idle' | 'listening' | 'transcribing' | 'thinking' | 'generating' | 'speaking'>('idle');
  const [notice, setNotice] = useState('');
  const [connectionNotice, setConnectionNotice] = useState('');
  const [playingMessageId, setPlayingMessageId] = useState('');
  const [liveLipSyncConfigured, setLiveLipSyncConfigured] = useState(false);
  const [liveLipSyncState, setLiveLipSyncState] = useState<'NOT_CONFIGURED' | 'NOT_PROBED' | 'UNAVAILABLE' | 'AVAILABLE'>('NOT_PROBED');
  const [voiceCloneConfigured, setVoiceCloneConfigured] = useState(false);
  const [lipSyncVideoUrl, setLipSyncVideoUrl] = useState('');
  const [lipSyncUnavailable, setLipSyncUnavailable] = useState(false);
  const [lipSyncDiagnostic, setLipSyncDiagnostic] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [availableLanguages, setAvailableLanguages] = useState<ConversationLanguage[]>(['en', 'te', 'hi']);
  const [expandedMessageId, setExpandedMessageId] = useState('');
  const [documentAnalyses, setDocumentAnalyses] = useState<DocumentAnalysisResponse[]>([]);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [selectedLandId, setSelectedLandId] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingTimeoutRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lipSyncVideoRef = useRef<HTMLVideoElement | null>(null);
  const lipSyncVideoUrlRef = useRef<string | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationRef = useRef<number | null>(null);
  const busyRef = useRef(false);
  const conversationRef = useRef<HTMLDivElement>(null);
  const documentInputRef = useRef<HTMLInputElement>(null);
  const lastLanguageRef = useRef<ConversationLanguage>('en');

  const busy = phase === 'transcribing' || phase === 'thinking' || phase === 'generating';
  const isRecording = phase === 'listening';
  const avatarState = getAvatarState(phase);

  const refreshLanguages = async () => {
    try {
      const status = await api.getModelsStatus();
      const supported = status.available_conversation_languages.filter(
        (language): language is ConversationLanguage =>
          SUPPORTED_LANGUAGES.includes(language as ConversationLanguage),
      );
      if (supported.length) setAvailableLanguages(supported);
      setConnectionNotice('');
    } catch {
      setConnectionNotice('I can’t reach the advisor service right now. Check your connection and try again.');
    }
  };

  useEffect(() => { void refreshLanguages(); }, []);

  useEffect(() => {
    let active = true;
    void api.getBhoomiAvatarStatus().then((status) => {
      if (!active) return;
      setLiveLipSyncConfigured(status.live_lipsync_configured);
      setLiveLipSyncState(status.live_lipsync_state);
      setVoiceCloneConfigured(status.voice_clone_configured);
      setLipSyncUnavailable(status.live_lipsync_state === 'UNAVAILABLE' || status.live_lipsync_state === 'NOT_CONFIGURED');
      setLipSyncDiagnostic(status.live_lipsync_message);
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  useEffect(() => {
    conversationRef.current?.scrollTo({ top: conversationRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, phase]);

  const stopPlayback = () => {
    if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    audioRef.current?.pause();
    audioRef.current = null;
    if (lipSyncVideoRef.current) {
      lipSyncVideoRef.current.pause();
      lipSyncVideoRef.current.currentTime = 0;
    }
    if (lipSyncVideoUrlRef.current) URL.revokeObjectURL(lipSyncVideoUrlRef.current);
    lipSyncVideoUrlRef.current = null;
    setLipSyncVideoUrl('');
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    audioUrlRef.current = null;
    const context = audioContextRef.current;
    audioContextRef.current = null;
    if (context && context.state !== 'closed') void context.close();
    setAudioLevel(0);
    setPlayingMessageId('');
    setPhase((current) => current === 'speaking' ? 'idle' : current);
  };

  useEffect(() => () => {
    if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    audioRef.current?.pause();
    lipSyncVideoRef.current?.pause();
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    if (lipSyncVideoUrlRef.current) URL.revokeObjectURL(lipSyncVideoUrlRef.current);
    if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    void audioContextRef.current?.close();
  }, []);

  const playReply = async (entry: ConversationEntry) => {
    const speech = entry.speech;
    if (!speech?.audio_base64) {
      setNotice(speech?.audio_error || 'Bhoomi’s voice is unavailable right now. You can still read her response.');
      return;
    }
    stopPlayback();
    setNotice('');
    let url: string | null = null;
    let audio: HTMLAudioElement | null = null;
    let context: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let mediaSource: MediaElementAudioSourceNode | null = null;
    let cleared = false;

    const clear = () => {
      if (cleared) return;
      cleared = true;
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
      if (audioRef.current === audio) audioRef.current = null;
      if (url && audioUrlRef.current === url) audioUrlRef.current = null;
      if (url) URL.revokeObjectURL(url);
      if (lipSyncVideoRef.current) {
        lipSyncVideoRef.current.pause();
        lipSyncVideoRef.current.currentTime = 0;
      }
      if (lipSyncVideoUrlRef.current) URL.revokeObjectURL(lipSyncVideoUrlRef.current);
      lipSyncVideoUrlRef.current = null;
      setLipSyncVideoUrl('');
      if (audioContextRef.current === context) audioContextRef.current = null;
      if (context && context.state !== 'closed') void context.close();
      setAudioLevel(0);
      setPlayingMessageId('');
      setPhase((current) => current === 'speaking' ? 'idle' : current);
    };

    try {
      const objectUrl = URL.createObjectURL(decodeTimbreWav(speech.audio_base64, 'audio/wav'));
      const playback = new Audio(objectUrl);
      url = objectUrl;
      audio = playback;
      playback.preload = 'auto';
      playback.muted = false;
      playback.volume = 1;
      audioRef.current = playback;
      audioUrlRef.current = objectUrl;
      setPlayingMessageId(entry.id);
      setPhase('generating');

      playback.onended = clear;
      playback.onerror = () => {
        clear();
        setNotice('Audio playback failed. Tap “Hear Bhoomi” to retry, or read her complete response.');
      };
      playback.onplaying = () => {
        setNotice('');
        setPhase('speaking');
      };

      const attachAudioAnalyser = async () => {
        if (typeof AudioContext === 'undefined') return;
        let candidate: AudioContext | null = null;
        try {
          candidate = new AudioContext();
          context = candidate;
          audioContextRef.current = candidate;
          await candidate.resume();
          if (candidate.state !== 'running' || audioRef.current !== playback) {
            if (audioContextRef.current === candidate) audioContextRef.current = null;
            if (candidate.state !== 'closed') await candidate.close();
            if (context === candidate) context = null;
            return;
          }

          const audioAnalyser = candidate.createAnalyser();
          audioAnalyser.fftSize = 512;
          mediaSource = candidate.createMediaElementSource(playback);
          try {
            mediaSource.connect(audioAnalyser);
            audioAnalyser.connect(candidate.destination);
          } catch {
            // A failed meter must never silence the actual media element.
            try { mediaSource.disconnect(); } catch { /* already disconnected */ }
            mediaSource.connect(candidate.destination);
            analyser = null;
            return;
          }
          analyser = audioAnalyser;
          const samples = new Uint8Array(audioAnalyser.fftSize);
          const measure = () => {
            if (!analyser || audioRef.current !== playback) return;
            analyser.getByteTimeDomainData(samples);
            let total = 0;
            for (const sample of samples) {
              const centered = (sample - 128) / 128;
              total += centered * centered;
            }
            setAudioLevel(Math.sqrt(total / samples.length));
            animationRef.current = requestAnimationFrame(measure);
          };
          measure();
        } catch {
          if (mediaSource && candidate) {
            try { mediaSource.disconnect(); } catch { /* already disconnected */ }
            try { mediaSource.connect(candidate.destination); } catch { /* direct graph fallback */ }
          } else if (candidate && candidate.state !== 'closed') {
            await candidate.close();
            if (audioContextRef.current === candidate) audioContextRef.current = null;
            if (context === candidate) context = null;
          }
          analyser = null;
        }
      };

      if (speech.lipSyncVideo) {
        const managedUrl = createManagedObjectUrl(speech.lipSyncVideo);
        lipSyncVideoUrlRef.current = managedUrl.url;
        setLipSyncVideoUrl(managedUrl.url);
        if (lipSyncVideoRef.current) lipSyncVideoRef.current.src = managedUrl.url;
      } else if (lipSyncVideoRef.current) {
        lipSyncVideoRef.current.src = BHOOMI_SPEAKING_VIDEO_URL;
      }
      await attachAudioAnalyser();
      const video = lipSyncVideoRef.current;
      if (video) {
        video.pause();
        video.currentTime = 0;
        video.muted = true;
        video.volume = 0;
        void video.play().catch(() => setNotice('Bhoomi’s speaking video could not play; her generated voice will continue.'));
      }
      const attempt = await attemptMediaPlayback(playback);
      if (attempt !== 'playing') {
        video?.pause();
        clear();
        setPhase('idle');
        setNotice(attempt === 'blocked'
          ? 'Your browser blocked automatic audio. Tap “Hear Bhoomi” to play the generated voice.'
          : 'The generated voice could not be played. Tap “Hear Bhoomi” to retry.');
      }
    } catch (error) {
      clear();
      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        setNotice('Your browser blocked automatic audio. Tap “Hear Bhoomi” to play this response.');
      } else {
        setNotice(error instanceof Error
          ? `Audio could not play: ${error.message}. Tap “Hear Bhoomi” to retry.`
          : 'Audio could not play. Tap “Hear Bhoomi” to retry.');
      }
    }
  };

  const runQuestion = async (
    rawQuestion: string,
    language: ConversationLanguage,
    transcriptAlreadyDisplayed = false,
    currentDocuments = documentAnalyses,
    uploadedDocument?: DocumentAnalysisResponse,
  ) => {
    const query = rawQuestion.trim();
    if (!query || busyRef.current) return;
    if (!availableLanguages.includes(language)) {
      setNotice(`Bhoomi cannot reply in ${getLanguageName(language)} right now. Please try a supported language.`);
      return;
    }
    stopPlayback();
    lastLanguageRef.current = language;
    busyRef.current = true;
    setNotice('');
    setQuestion('');
    setPhase('thinking');
    const history = messages
      .filter((message) => message.id !== 'welcome')
      .slice(-60)
      .map(({ role, text }) => ({ role, content: text }));
    if (!transcriptAlreadyDisplayed) {
      setMessages((current) => [...current, {
        id: newMessageId('user'),
        role: 'user',
        text: query,
        document: uploadedDocument,
      }]);
    }

    try {
      const result = await api.investigate(
        query,
        language,
        selectedLandId || undefined,
        history,
        currentDocuments,
      );
      setConnectionNotice('');
      const speech: NonNullable<ConversationEntry['speech']> = { ...getBhoomiReply(result.dialogue_sequence) };
      setSelectedLandId(result.matched_land_ids.length === 1 ? result.matched_land_ids[0] : '');
      setPhase('generating');
      try {
        const audio = await api.speakText(speech.text, language);
        speech.audio_base64 = audio.audio_base64;
        speech.audio_error = undefined;
        if (liveLipSyncConfigured) {
          try {
            speech.lipSyncVideo = await api.generateBhoomiLipSync(decodeTimbreWav(audio.audio_base64));
            setLipSyncUnavailable(false);
            setLiveLipSyncState('AVAILABLE');
            setLipSyncDiagnostic('A synchronized video was returned for Bhoomi’s latest response.');
          } catch (lipSyncError) {
            speech.lipSyncError = lipSyncError instanceof Error
              ? lipSyncError.message
              : 'Bhoomi live lip-sync is unavailable.';
            setLipSyncUnavailable(true);
            setLiveLipSyncState('UNAVAILABLE');
            setLipSyncDiagnostic(speech.lipSyncError);
          }
        } else {
          setLipSyncUnavailable(true);
          setLiveLipSyncState('NOT_CONFIGURED');
          setLipSyncDiagnostic('Live lip-sync is not configured. Timbre voice playback remains available.');
        }
      } catch (audioError) {
        speech.audio_base64 = undefined;
        speech.audio_error = audioError instanceof Error ? audioError.message : 'Timbre could not generate audio.';
      }
      const response: ConversationEntry = {
        id: newMessageId('assistant'),
        role: 'assistant',
        text: speech.text,
        speech,
        report: result.investigation_report,
      };
      setMessages((current) => [...current, response]);
      setExpandedMessageId('');
      setPhase('idle');
      if (speech.audio_base64) void playReply(response);
      else if (speech.audio_error) setNotice(speech.audio_error);
      // Lip-sync availability is shown beneath the avatar instead of repeating
      // a warning banner in chat after every turn.
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Bhoomi could not complete that response. Please try again.');
      setPhase('idle');
    } finally {
      busyRef.current = false;
    }
  };

  const handleDocumentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file || uploadingDocument || busyRef.current) return;
    if (documentAnalyses.length >= 10) {
      setNotice('This conversation already has 10 document scans. Start a new conversation to add more.');
      return;
    }

    setUploadingDocument(true);
    setNotice('');
    try {
      const analysis = await api.analyzeDocument(file);
      const updatedDocuments = [...documentAnalyses, analysis];
      setDocumentAnalyses(updatedDocuments);
      await runQuestion(
        `I shared the document “${file.name}”. Please review its preliminary text-scan findings and tell me what I should verify.`,
        lastLanguageRef.current,
        false,
        updatedDocuments,
        analysis,
      );
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'The document could not be analyzed. Please try again.');
    } finally {
      setUploadingDocument(false);
    }
  };

  const downloadReport = async () => {
    if (downloadingReport) return;
    const history = messages
      .filter((message) => message.id !== 'welcome')
      .slice(-60)
      .map(({ role, text }) => ({ role, content: text }));
    setDownloadingReport(true);
    setNotice('');
    try {
      await api.downloadInvestigationReport(history, selectedLandId || undefined, documentAnalyses);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'The report could not be generated. Please try again.');
    } finally {
      setDownloadingReport(false);
    }
  };

  const transcribeRecording = async (recording: Blob) => {
    setNotice('');
    setPhase('transcribing');
    try {
      const context = new AudioContext();
      try {
        const buffer = await context.decodeAudioData(await recording.arrayBuffer());
        if (buffer.duration > 30) {
          setNotice('Please keep voice messages under 30 seconds.');
          setPhase('idle');
          return;
        }
        const { blob, rms } = encodeAudioBufferAsWav(buffer);
        if (rms < 0.003) {
          setNotice('I couldn’t hear speech. Please try again a little closer to your microphone.');
          setPhase('idle');
          return;
        }
        const result = await api.transcribeAudio(blob);
        if (!result.transcript.trim()) {
          setNotice('I didn’t catch that. Please try speaking again.');
          setPhase('idle');
          return;
        }
        setMessages((current) => [...current, {
          id: newMessageId('user'),
          role: 'user',
          text: result.transcript,
        }]);
        const language = getDetectedLanguage(result.detected_language);
        if (!language) {
          setNotice('I heard your voice, but could not identify a supported language. Please try again.');
          setPhase('idle');
          return;
        }
        await runQuestion(result.transcript, language, true);
      } finally {
        await context.close();
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'I couldn’t understand that recording. Please try again.');
      setPhase('idle');
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current);
      recordingTimeoutRef.current = null;
      if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop();
      return;
    }
    if (busyRef.current) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setNotice('This browser does not support microphone recording. You can type your question instead.');
      return;
    }
    stopPlayback();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const preferredType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
        .find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, preferredType ? { mimeType: preferredType } : undefined);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      let recordingFailed = false;
      recorder.ondataavailable = (event) => {
        if (event.data.size) audioChunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        recordingFailed = true;
        if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = null;
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setPhase('idle');
        setNotice('Microphone recording failed. Please try again or type your question.');
      };
      recorder.onstop = () => {
        if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = null;
        const recording = new Blob(audioChunksRef.current, { type: recorder.mimeType });
        mediaRecorderRef.current = null;
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (recordingFailed) return;
        if (recording.size) void transcribeRecording(recording);
        else {
          setPhase('idle');
          setNotice('No recording was captured. Please try again.');
        }
      };
      recorder.start();
      setNotice('');
      setPhase('listening');
      recordingTimeoutRef.current = window.setTimeout(() => {
        if (recorder.state === 'recording') recorder.stop();
      }, 25_000);
    } catch (error) {
      if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current);
      recordingTimeoutRef.current = null;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      mediaRecorderRef.current = null;
      const name = error instanceof Error ? error.name : '';
      setNotice(name === 'NotAllowedError'
        ? 'Microphone access is blocked. Allow it in your browser settings, then try again.'
        : name === 'NotFoundError'
          ? 'No microphone was found. Connect a microphone or type your question.'
          : error instanceof Error ? error.message : 'Microphone access is unavailable.');
      setPhase('idle');
    }
  };

  const submitQuestion = (event: FormEvent) => {
    event.preventDefault();
    void runQuestion(question, detectTypedLanguage(question));
  };

  const statusText = ({
    idle: 'Ready when you are',
    listening: 'I’m listening…',
    transcribing: 'Let me hear that clearly…',
    thinking: 'Let me think that through…',
    generating: 'Preparing Bhoomi’s voice…',
    speaking: 'Bhoomi is speaking',
  })[phase];
  const visibleNotice = notice || connectionNotice;

  return (
    <div className="conversation-experience">
      <header className="conversation-header">
        <div className="conversation-brand" aria-label="BhoomiVaani">
          <span className="brand-leaf" aria-hidden="true">b</span>
          <span>BhoomiVaani</span>
        </div>
        <p>Your land-buying advisor</p>
        <span className="header-presence"><i /> Here with you</span>
        {messages.some((message) => message.role === 'user') && (
          <button
            type="button"
            className="report-download"
            onClick={() => void downloadReport()}
            disabled={downloadingReport}
          >
            <Download size={16} />
            <span>{downloadingReport ? 'Preparing report…' : 'Download report'}</span>
          </button>
        )}
      </header>

      <main className="conversation-main">
        <section className={`advisor-stage advisor-${avatarState}`} aria-label="Bhoomi, your AI land-buying advisor">
          <div className="avatar-frame">
            <BhoomiAvatar
              state={avatarState}
              audioLevel={audioLevel}
              speakingVideoUrl={lipSyncVideoUrl}
              videoRef={lipSyncVideoRef}
              onVideoError={() => setNotice('Bhoomi’s speaking video failed; her actual audio playback remains available.')}
            />
          </div>
          <div className="advisor-intro">
            <h1>Bhoomi</h1>
            <span className="advisor-presence"><i /> {phase === 'speaking' && !lipSyncVideoUrl
              ? 'Voice playing · no live mouth sync'
              : statusText}</span>
            <p className="avatar-service-status">
              Gnani voice {voiceCloneConfigured ? 'configured' : 'not configured'} · {liveLipSyncState === 'AVAILABLE'
                ? 'lip-sync available'
                : liveLipSyncState === 'NOT_CONFIGURED'
                  ? 'voice only · lip-sync not configured'
                  : liveLipSyncState === 'UNAVAILABLE' || lipSyncUnavailable
                    ? 'voice only · lip-sync unavailable'
                    : 'lip-sync adapter configured · not yet verified'}
              {lipSyncDiagnostic && <span role="status">{lipSyncDiagnostic}</span>}
            </p>
          </div>
          <button
            type="button"
            className={`voice-button ${isRecording ? 'voice-recording' : ''}`}
            onClick={() => void toggleRecording()}
            disabled={busy || uploadingDocument}
            aria-label={isRecording ? 'Stop voice recording' : 'Start voice recording'}
          >
            {isRecording ? <MicOff size={25} strokeWidth={1.8} /> : <Mic size={25} strokeWidth={1.8} />}
            <span className="voice-pulse" />
          </button>
          <span className="voice-instruction">
            {isRecording ? 'Tap when you’ve finished speaking' : 'Tap to talk with Bhoomi'}
          </span>
        </section>

        <section className="conversation-panel" aria-label="Conversation with Bhoomi">
          <div className="chat-panel-header">
            <strong>Conversation with Bhoomi</strong>
            <span>{statusText}</span>
          </div>
          <div className="conversation-scroll" ref={conversationRef} aria-live="polite">
            {messages.map((message, index) => (
              <article className={`message message-${message.role}`} key={message.id}>
                {message.role === 'assistant' && (
                  <div className="message-avatar" aria-hidden="true">b</div>
                )}
                <div className="message-body">
                  {index > 0 && <span className="message-name">{message.role === 'assistant' ? 'Bhoomi' : 'You'}</span>}
                  <p>{message.text}</p>
                  {message.document && (
                    <div className="document-scan-result">
                      <strong>Text-pattern scan · {message.document.risk_level}</strong>
                      <p>{message.document.summary}</p>
                      {message.document.detected_issues.map((issue, issueIndex) => (
                        <p key={`${issue.issue_title}-${issueIndex}`}>
                          <b>{issue.issue_title}:</b> {issue.explanation}
                        </p>
                      ))}
                      <small>{message.document.disclaimer}</small>
                    </div>
                  )}
                  {message.role === 'assistant' && message.speech?.audio_base64 && (
                    <button
                      type="button"
                      className="message-audio"
                      onClick={() => playingMessageId === message.id ? stopPlayback() : void playReply(message)}
                    >
                      {playingMessageId === message.id ? <VolumeX size={16} /> : <Volume2 size={16} />}
                      {playingMessageId === message.id ? 'Stop voice' : 'Hear Bhoomi'}
                    </button>
                  )}
                  {message.role === 'assistant' && message.report && (
                    <div className="evidence-disclosure">
                      <button
                        type="button"
                        aria-expanded={expandedMessageId === message.id}
                        onClick={() => setExpandedMessageId((current) => current === message.id ? '' : message.id)}
                      >
                        What I checked <ChevronDown size={16} />
                      </button>
                      {expandedMessageId === message.id && (
                        <div className="evidence-details">
                          <p>{message.report.disclaimer}</p>
                          <p><b>Title:</b> {message.report.ownership_and_title.detail}</p>
                          <p><b>Documents:</b> {message.report.document_analysis.detail}</p>
                          {message.report.broker_claims?.map((claim, claimIndex) => (
                            <div className="broker-claim-evidence" key={`${claim.claim}-${claimIndex}`}>
                              <p><b>Broker claim:</b> {claim.claim}</p>
                              <p>
                                <b>Status:</b>{' '}
                                <span className={`claim-status claim-status-${claim.status.toLowerCase()}`}>
                                  {getEvidenceStatusLabel(claim.status)}
                                </span>
                              </p>
                              <p><b>Evidence reviewed:</b> {claim.evidence}</p>
                              {claim.missing_information.map((item) => (
                                <p key={item}><b>Missing:</b> {item}</p>
                              ))}
                              {claim.required_checks.map((item) => (
                                <p key={item}><b>Check:</b> {item}</p>
                              ))}
                            </div>
                          ))}
                          {message.report.recommended_next_steps.slice(0, 3).map((step) => <p key={step}>• {step}</p>)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </article>
            ))}
            {busy && (
              <div className="advisor-thinking" role="status">
                <span /><span /><span />
                <p>{phase === 'transcribing' ? 'Processing your recording' : phase === 'generating' ? 'Generating Bhoomi’s voice' : 'Bhoomi is thinking'}</p>
              </div>
            )}
          </div>
          <section className="conversation-composer" aria-label="Ask Bhoomi">
          {visibleNotice && (
            <div className="conversation-notice" role="status">
              <AlertCircle size={18} />
              <span>{visibleNotice}</span>
              {connectionNotice && (
                <button type="button" aria-label="Retry connection" onClick={() => void refreshLanguages()}>
                  <RotateCcw size={16} />
                </button>
              )}
            </div>
          )}
          <form className="text-composer" onSubmit={submitQuestion}>
            <input
              ref={documentInputRef}
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              className="visually-hidden"
              onChange={(event) => void handleDocumentUpload(event)}
              aria-label="Upload a land document"
              tabIndex={-1}
            />
            <button
              type="button"
              className="document-upload-button"
              onClick={() => documentInputRef.current?.click()}
              disabled={busy || uploadingDocument}
              aria-label={uploadingDocument ? 'Analyzing document' : 'Upload a land document'}
              title={uploadingDocument ? 'Analyzing document' : 'Upload a land document'}
            >
              <FileUp size={18} />
            </button>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Or type what you’d like to know…"
              aria-label="Type a question for Bhoomi"
              disabled={busy || isRecording || uploadingDocument}
            />
            <button type="submit" disabled={!question.trim() || busy || isRecording || uploadingDocument} aria-label="Send question">
              <ArrowUp size={19} />
            </button>
          </form>
          </section>
        </section>
      </main>
      <footer className="conversation-footer">
        <span>Take your time. We’ll work through it together.</span>
      </footer>
    </div>
  );
};
