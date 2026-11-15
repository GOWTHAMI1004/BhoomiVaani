import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  MicOff, 
  Send, 
  Volume2, 
  VolumeX, 
  Sparkles, 
  RotateCcw, 
  AlertTriangle, 
  Milestone, 
  TrendingUp, 
  CheckCircle,
  Play,
  Pause,
  HelpCircle,
  Languages
} from 'lucide-react';
import { Language, ConversationMessage, AIChatResponse } from '../types';
import { getTranslation } from '../translations/i18n';
import { api } from '../services/api';
import { encodeAudioBufferAsWav } from '../services/audio';

interface VoiceAssistantProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  onMatchedLands: (landIds: string[]) => void;
  autoPlayAudio: boolean;
  onSelectLandModal?: (landId: string) => void;
}

export const VoiceAssistant: React.FC<VoiceAssistantProps> = ({
  language,
  setLanguage,
  onMatchedLands,
  autoPlayAudio,
  onSelectLandModal
}) => {
  const t = getTranslation(language);

  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<'stt' | 'reasoning' | null>(null);
  const [textInput, setTextInput] = useState('');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // History state
  const [messages, setMessages] = useState<ConversationMessage[]>([
    {
      role: 'assistant',
      content: language === 'te' 
        ? "నమస్కారం! నేను భూమివాణి వాయిస్ అసిస్టెంట్‌ని. తెలంగాణ మరియు హైదరాబాద్ పరిసరాల్లో భూమి వివరాలు, లీగల్ టైటిల్ భద్రత మరియు మౌలిక సదుపాయాల వాస్తవాలను తనిఖీ చేయడానికి మాట్లాడండి లేదా టైప్ చేయండి."
        : language === 'hi'
        ? "नमस्ते! मैं भूमिवाणी वॉयस असिस्टेंट हूं। हैदराबाद व तेलंगाना में कृषि भूमि के कानूनी दस्तावेज, बैंक बकाया और हाईवे दावों की जांच के लिए बोलें या लिखें।"
        : "Namaste! I am BhoomiVaani, your voice-first land-awareness guide. Ask about a synthetic demo parcel, documents to request, or an unverified infrastructure claim.",
      ai_mode: "BHOOMIVAANI",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Clean up audio URL
  useEffect(() => {
    return () => {
      if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
      }
    };
  }, [currentAudioUrl]);

  const playAudioBase64 = (base64Data: string) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
      }

      // Convert base64 to binary blob
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'audio/wav' });

      if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
      }

      const url = URL.createObjectURL(blob);
      setCurrentAudioUrl(url);

      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onplay = () => setIsPlayingAudio(true);
      audio.onended = () => setIsPlayingAudio(false);
      audio.onerror = () => setIsPlayingAudio(false);

      audio.play().catch(e => {
        console.warn('Audio auto-play blocked or error:', e);
        setIsPlayingAudio(false);
      });
    } catch (e) {
      console.error('Error playing base64 audio:', e);
      setIsPlayingAudio(false);
    }
  };

  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    }
  };

  const handleSendQuery = async (queryText: string, responseLanguage?: Language) => {
    if (!queryText.trim()) return;

    const conversationLanguage = responseLanguage || language;

    // Add user message
    const userMsg: ConversationMessage = {
      role: 'user',
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setTextInput('');
    setIsLoading(true);
    setLoadingStage('reasoning');

    try {
      // Keep recent turns for the configured reasoning provider.
      const historyPayload = messages.slice(-6).map(m => ({
        role: m.role,
        content: m.content
      }));

      const res = await api.chatWithReasoning(queryText, conversationLanguage, historyPayload);

      // Trigger highlight of matched lands
      if (res.matched_land_ids && res.matched_land_ids.length > 0) {
        onMatchedLands(res.matched_land_ids);
      }

      const assistantMsg: ConversationMessage = {
        role: 'assistant',
        content: res.response,
        transcript: res.transcript,
        matched_land_ids: res.matched_land_ids,
        legal_warnings: res.legal_warnings,
        infrastructure_findings: res.infrastructure_findings,
        growth_insights: res.growth_insights,
        audio_base64: res.audio_base64,
        ai_mode: res.ai_mode,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMsg]);

      // Play audio response if available and autoplay enabled
      if (autoPlayAudio && res.audio_base64) {
        playAudioBase64(res.audio_base64);
      }
    } catch (err: any) {
      console.error('AI Chat Error:', err);
      const errMsg: ConversationMessage = {
        role: 'assistant',
        content: `Error communicating with BhoomiVaani AI: ${err.message || 'Server connection failed'}. Please check if backend is running.`,
        ai_mode: 'SYSTEM ERROR',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
      setLoadingStage(null);
    }
  };

  // Microphone recording simulation & Web Audio recording
  const handleToggleRecord = async () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    } else {
      setVoiceError(null);
      try {
        if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
          setVoiceError('This browser does not support microphone recording. Type your question instead.');
          return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const recording = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });
          stream.getTracks().forEach(track => track.stop());
          if (!recording.size) {
            setVoiceError('No audio was recorded. Try again or type your question.');
            return;
          }
          setIsLoading(true);
          setLoadingStage('stt');
          try {
            const audioContext = new AudioContext();
            try {
              const buffer = await audioContext.decodeAudioData(await recording.arrayBuffer());
              if (buffer.duration > 30) {
                setVoiceError('Recordings must be 30 seconds or shorter. Try again.');
                return;
              }
              const { blob, rms } = encodeAudioBufferAsWav(buffer);
              if (rms < 0.003) {
                setVoiceError('No speech was detected. Try again or type your question.');
                return;
              }
              const sttRes = await api.transcribeAudio(blob);
              if (!sttRes.transcript.trim()) {
                setVoiceError('No transcript was returned. Try recording again.');
                return;
              }
              const detectedLanguage = sttRes.detected_language?.split('-')[0]?.toLowerCase() || language;
              const nextLanguage = ['en', 'hi', 'te', 'ta', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa'].includes(detectedLanguage)
                ? detectedLanguage as Language
                : language;
              await handleSendQuery(sttRes.transcript, nextLanguage);
            } finally {
              await audioContext.close();
            }
          } catch (err) {
            setVoiceError(err instanceof Error ? err.message : 'Speech recognition failed. Try again or type your question.');
          } finally {
            setIsLoading(false);
            setLoadingStage(null);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        setVoiceError(err instanceof Error && err.name === 'NotAllowedError'
          ? 'Microphone access was denied. Allow microphone access or type your question.'
          : err instanceof Error ? err.message : 'Microphone could not be started.');
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-3xl border border-ivory-border shadow-elevated overflow-hidden">
      {/* Assistant Header */}
      <div className="p-4 bg-forest-950 text-white border-b border-forest-900 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-gold to-gold-light text-forest-950 flex items-center justify-center font-black shadow-gold-glow">
              <Sparkles className="w-5 h-5 text-forest-950" />
            </div>
            {isRecording && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
            )}
          </div>
          <div>
            <h3 className="font-bold text-sm tracking-tight font-serif flex items-center gap-1.5">
              <span>{t.aiVoiceAssistant}</span>
              <span className="text-[9px] bg-gold/20 text-gold-light border border-gold/40 px-1 py-0.2 rounded font-mono">
                Demo mode
              </span>
            </h3>
            <p className="text-[11px] text-gray-300">
              Prisma STT • Timbre TTS
            </p>
          </div>
        </div>

        {/* Clear / Reset button */}
        <button
          onClick={() => {
            setMessages([messages[0]]);
            onMatchedLands([]);
            handleStopAudio();
          }}
          title="Reset Conversation"
          aria-label="Reset Conversation"
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-forest-900 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Demo Prompts Bar */}
      <div className="bg-ivory-dark/60 p-2.5 border-b border-ivory-border">
        <div className="flex items-center gap-1 text-[11px] font-bold text-gray-600 mb-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-forest-800" />
          <span>{t.demoPromptsTitle}</span>
        </div>
        <div className="flex flex-col gap-1.5">
          <button
            onClick={() => handleSendQuery(t.demo1)}
            className="text-left text-[11px] px-2.5 py-1.5 rounded-lg bg-white border border-ivory-border text-forest-950 hover:border-gold hover:bg-gold-light/10 font-medium transition-all truncate shadow-2xs"
          >
            1. "{t.demo1}"
          </button>
          <button
            onClick={() => handleSendQuery(t.demo2)}
            className="text-left text-[11px] px-2.5 py-1.5 rounded-lg bg-white border border-ivory-border text-forest-950 hover:border-rose-400 hover:bg-rose-50/50 font-medium transition-all truncate shadow-2xs"
          >
            2. "{t.demo2}"
          </button>
          <button
            onClick={() => handleSendQuery(t.demo3)}
            className="text-left text-[11px] px-2.5 py-1.5 rounded-lg bg-white border border-ivory-border text-forest-950 hover:border-forest-600 hover:bg-forest-50 font-medium transition-all truncate shadow-2xs"
          >
            3. "{t.demo3}"
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-ivory/40">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={index}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
            >
              <div
                className={`max-w-[92%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-sm ${
                  isUser
                    ? 'bg-forest-900 text-white rounded-br-none'
                    : 'bg-white border border-ivory-border text-gray-800 rounded-bl-none shadow-soft'
                }`}
              >
                {!isUser && msg.ai_mode && (
                  <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1.5 pb-1 border-b border-gray-100 font-mono">
                    <span className="text-forest-800 font-bold">BhoomiVaani AI</span>
                    <span className="bg-forest-50 text-forest-800 px-1 rounded">{msg.ai_mode}</span>
                  </div>
                )}

                <p className="whitespace-pre-line text-sm">{msg.content}</p>

                {/* Structured Findings Boxes */}
                {!isUser && msg.legal_warnings && msg.legal_warnings.length > 0 && (
                  <div className="mt-2.5 p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-950 text-[11px] space-y-1">
                    <div className="flex items-center gap-1 font-bold text-rose-900">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                      <span>Legal Due Diligence Warnings:</span>
                    </div>
                    {msg.legal_warnings.map((w, idx) => (
                      <div key={idx} className="pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-rose-500">
                        {w}
                      </div>
                    ))}
                  </div>
                )}

                {!isUser && msg.infrastructure_findings && msg.infrastructure_findings.length > 0 && (
                  <div className="mt-2 p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-950 text-[11px] space-y-1">
                    <div className="flex items-center gap-1 font-bold text-emerald-900">
                      <Milestone className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                      <span>Infrastructure Claim Verification:</span>
                    </div>
                    {msg.infrastructure_findings.map((inf, idx) => (
                      <div key={idx} className="pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-emerald-500">
                        {inf}
                      </div>
                    ))}
                  </div>
                )}

                {!isUser && msg.matched_land_ids && msg.matched_land_ids.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-gray-100 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-gray-500 font-bold uppercase">Matched Lands:</span>
                    {msg.matched_land_ids.map((lid) => (
                      <span
                        key={lid}
                        onClick={() => onSelectLandModal && onSelectLandModal(lid)}
                        className="px-2 py-0.5 rounded-md font-mono text-[10px] font-bold bg-gold/15 text-gold-dark border border-gold/40 cursor-pointer hover:bg-gold hover:text-white transition-colors"
                      >
                        {lid}
                      </span>
                    ))}
                  </div>
                )}

                {/* Audio playback button on assistant messages */}
                {!isUser && msg.audio_base64 && (
                  <div className="mt-2 pt-1.5 flex items-center justify-between text-[11px] text-forest-800">
                    <button
                      onClick={() => playAudioBase64(msg.audio_base64!)}
                      className="flex items-center gap-1 font-semibold text-forest-800 hover:text-forest-950 bg-forest-50 px-2.5 py-1 rounded-lg border border-forest-200/60"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                      <span>Play Voice Response (Timbre v2.5)</span>
                    </button>
                  </div>
                )}
              </div>

              <span className="text-[10px] text-gray-400 px-1 font-mono">
                {msg.timestamp}
              </span>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start space-y-1">
            <div className="bg-white border border-ivory-border rounded-2xl p-3.5 shadow-soft flex items-center gap-3 text-xs text-gray-600">
              <div className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-forest-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-forest-700"></span>
              </div>
              <span className="font-medium animate-pulse">
                {loadingStage === 'stt' ? t.listening : t.processing}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Voice Mic & Controls Panel */}
      <div className="p-4 bg-white border-t border-ivory-border space-y-3">
        {voiceError && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-900" role="status">
            {voiceError}
          </div>
        )}
        {/* Animated Microphone Action */}
        <div className="flex flex-col items-center justify-center py-1">
          <div className="relative">
            {isRecording && (
              <>
                <div className="absolute inset-0 rounded-full bg-rose-500/20 animate-ripple"></div>
                <div className="absolute inset-0 rounded-full bg-rose-500/30 animate-ping"></div>
              </>
            )}

            <button
              onClick={handleToggleRecord}
              disabled={isLoading}
              className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 shadow-elevated ${
                isRecording
                  ? 'bg-rose-600 text-white scale-110 shadow-rose-500/40'
                  : 'bg-gradient-to-tr from-forest-950 to-forest-800 text-gold hover:scale-105 shadow-forest-glow'
              }`}
            >
              {isRecording ? (
                <MicOff className="w-7 h-7 animate-pulse" />
              ) : (
                <Mic className="w-7 h-7" />
              )}
            </button>
          </div>

          <div className="text-center mt-2">
            <span className={`text-xs font-bold ${isRecording ? 'text-rose-600 animate-pulse' : 'text-gray-700'}`}>
              {isRecording ? t.listening : t.pressToSpeak}
            </span>
            <div className="text-[10px] text-gray-400 font-mono">Gnani Prisma v2.5 · real provider required</div>
          </div>
        </div>

        {/* Text Input Fallback */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery(textInput);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={t.typeQuery}
            disabled={isLoading || isRecording}
            className="flex-1 px-3.5 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-forest-800 focus:border-transparent bg-ivory-dark/30 placeholder-gray-400"
          />
          <button
            type="submit"
            disabled={!textInput.trim() || isLoading || isRecording}
            aria-label="Send query"
            className="p-2.5 rounded-xl bg-forest-900 text-white hover:bg-forest-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0 shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
