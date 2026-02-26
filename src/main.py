#!/usr/bin/env python3
"""
VoiceTry - Modular Voice AI Terminal

A voice-powered AI assistant with real-time visualization.
Orchestrates 4 independent modules: speech_to_text, llm_processor, text_to_speech, ui
"""

import asyncio
import os
import sys
import time
import threading
import queue
from collections import deque
from pathlib import Path
from typing import Optional, Union

import numpy as np

# Fix OpenMP conflict on macOS - must be set before importing any OpenMP-dependent libs
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
# Suppress PyTorch version warnings
os.environ["TORCH_CPP_MIN_LOG_LEVEL"] = "2"

# Ensure src directory is in path for module resolution
# When running as `python3 -m src.main`, we need src/ accessible
script_dir = Path(__file__).parent.absolute()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Also ensure parent directory is in path for 'src.speech_to_text' style imports if needed
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live

# Import from local modules (all modules are in src/)
from speech_to_text import Recorder, Transcriber, SpeechToTextConfig
from llm_processor import DeepSeekLLM
from text_to_speech import TTSPlayer, TTSConfig, VoiceSelector, get_synthesizer, TTSEngine
from ui import VoiceTerminalUI, UIAnimator, AppState


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner(console: Console) -> None:
    """Print startup banner."""
    console.clear()

    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██╗   ██╗ ██████╗ ██╗ ██████╗████████╗██████╗  █████╗[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║   ██║██╔═══██╗██║██╔════╝╚══██╔══╝╚════██╗██╔══██╗[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║   ██║██║   ██║██║██║        ██║    █████╔╝███████║[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]╚██╗ ██╔╝██║   ██║██║██║        ██║   ██╔═══╝ ██╔══██║[/]  [bold cyan]║[/]
[bold cyan]║[/]   [bold white]╚████╔╝ ╚██████╔╝██║╚██████╗   ██║   ███████╗██║  ██║[/]  [bold cyan]║[/]
[bold cyan]║[/]    [bold white]╚═══╝   ╚═════╝ ╚═╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/]  [bold cyan]║[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]║[/]  [dim]━━━━━━━━━━━━━━━━ Voice AI Terminal v2.0 ━━━━━━━━━━━━━━━━[/]  [bold cyan]║[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]
    """
    console.print(banner)

    # Print instructions
    console.print()
    console.print("[bold cyan]📋 Instructions:[/]")
    console.print("  [bold green]1.[/] Press [bold yellow]ENTER[/] to start the voice terminal")
    console.print("  [bold green]2.[/] Press [bold yellow]SPACE[/] to start/stop recording")
    console.print("  [bold green]3.[/] Press [bold yellow]S[/] or [bold yellow]C[/] to stop/cancel a response")
    console.print("  [bold green]4.[/] Press [bold yellow]V[/] to change voice")
    console.print("  [bold green]5.[/] Press [bold yellow]E[/] to switch TTS engine")
    console.print("  [bold green]6.[/] Press [bold yellow]Q[/] to quit")
    console.print()


def get_keypress() -> str:
    """Get a single keypress without waiting for enter and without terminal echo."""
    try:
        import readchar
        import tty
        import termios
        import sys
        
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            # Set terminal to raw mode, no echo
            tty.setcbreak(sys.stdin.fileno())
            # Read a single character
            key = readchar.readkey()
            return key
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except Exception:
        # Fallback - just read without echo control
        try:
            import readchar
            return readchar.readkey()
        except ImportError:
            return input().strip().lower()


class VoiceTryApp:
    """Main application class orchestrating all modules."""

    def __init__(self):
        load_dotenv()

        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

        self.console = Console(force_terminal=True, no_color=False)
        self.ui = VoiceTerminalUI()
        self.voice_selector = VoiceSelector(self.console)

        self._recorder: Optional[Recorder] = None
        self._transcriber: Optional[Transcriber] = None
        self._llm: Optional[DeepSeekLLM] = None
        self._synthesizer: Optional[TTSEngine] = None
        self._player: Optional[TTSPlayer] = None
        self._tts_warmed_up = False
        self._exit_requested = False

        self._key_queue: queue.Queue[str] = queue.Queue()
        self._key_listener_thread = threading.Thread(
            target=self._key_listener, daemon=True
        )
        self._key_listener_thread.start()

        self._latency_history = deque(maxlen=20)

    def _key_listener(self) -> None:
        """Continuously read keypresses and enqueue them."""
        while True:
            try:
                key = get_keypress()
                self._key_queue.put(key)
            except Exception:
                pass

    def _get_next_key(self) -> str:
        """Blocking read of next queued key."""
        return self._key_queue.get()

    def _drain_keys(self) -> list[str]:
        """Drain any queued keys (non-blocking)."""
        keys: list[str] = []
        while True:
            try:
                keys.append(self._key_queue.get_nowait())
            except queue.Empty:
                break
        return keys

    @property
    def recorder(self) -> Recorder:
        if self._recorder is None:
            config = SpeechToTextConfig()
            self._recorder = Recorder(config)
            self._recorder.set_level_callback(self._on_audio_level)
        return self._recorder

    @property
    def transcriber(self) -> Transcriber:
        if self._transcriber is None:
            self.console.print("[dim]Loading Whisper model...[/]")
            config = SpeechToTextConfig()
            self._transcriber = Transcriber(config)
        return self._transcriber

    @property
    def llm(self) -> DeepSeekLLM:
        if self._llm is None:
            self._llm = DeepSeekLLM(
                api_key=self.deepseek_api_key,
                model=self.deepseek_model,
                system_prompt=self._get_system_prompt(),
                temperature=0.7,
                max_tokens=2048,
            )
        return self._llm

    @property
    def synthesizer(self):
        if self._synthesizer is None:
            config = self.voice_selector.get_config()
            self.console.print(f"[dim]Loading {config.engine.upper()} TTS...[/]")
            self._synthesizer = get_synthesizer(config)
        return self._synthesizer

    @property
    def player(self) -> TTSPlayer:
        if self._player is None:
            config = self.voice_selector.get_config()
            self._player = TTSPlayer(config)
            self._player.set_level_callback(self._on_audio_level)
        return self._player

    def _get_system_prompt(self) -> str:
        return """You are a helpful, friendly AI assistant. You respond concisely 
and naturally, as if having a voice conversation. Keep responses relatively brief 
(2-4 sentences typically) since they will be spoken aloud. Be engaging and helpful."""

    def _on_audio_level(self, level: float) -> None:
        self.ui.update_audio_level(level)

    def run(self) -> None:
        """Run the main application loop."""
        clear_screen()
        print_banner(self.console)

        self.console.print()
        self.console.print("[bold green]✓[/] Initializing modules...")
        self.console.print("[dim]  • DeepSeek API: Connected[/]")
        self.console.print("[dim]  • Whisper: Ready (will load on first use)[/]")
        self.console.print(f"[dim]  • {self.voice_selector.current_engine.upper()} TTS: Ready (will load on first use)[/]")
        self.console.print()
        self.console.print("[bold cyan]Press ENTER to start the voice terminal...[/]")
        # Wait for ENTER using queued keys
        while True:
            key = self._get_next_key()
            if key in ("\r", "\n"):
                break

        with Live(self.ui.render(), console=self.console, refresh_per_second=10) as live:
            animator = UIAnimator(self.ui, live)
            animator.start()

            try:
                self._main_loop()
            except KeyboardInterrupt:
                pass
            finally:
                animator.stop()

    def _main_loop(self) -> None:
        """Main interaction loop."""
        while True:
            if self._exit_requested:
                break
            key = self._get_next_key()

            if key.lower() == 'q':
                break

            if key.lower() == 'e':
                self._handle_engine_selection()

            if key.lower() == 'v':
                self._handle_voice_selection()

            if key == ' ':
                self._handle_recording()

    def _handle_engine_selection(self) -> None:
        """Handle TTS engine selection menu."""
        # Don't allow engine change while speaking
        if self._player and self._player.is_playing:
            self.console.print("\n[yellow]Cannot change engine while speaking. Wait for audio to finish.[/]")
            return
        
        self.voice_selector.select_engine()
        # Reset synthesizer and player to reload with new engine
        self._synthesizer = None
        self._player = None

    def _handle_voice_selection(self) -> None:
        """Handle voice selection menu."""
        # Don't allow voice change while speaking
        if self._player and self._player.is_playing:
            self.console.print("\n[yellow]Cannot change voice while speaking. Wait for audio to finish.[/]")
            return
        
        selected = self.voice_selector.select_voice()
        self._synthesizer = None
        self._player = None

    def _handle_recording(self) -> None:
        """Handle recording, transcribing, and responding."""
        turn_t0 = time.perf_counter()
        self.ui.set_state(AppState.RECORDING)
        
        try:
            self.recorder.start_recording()
        except Exception as e:
            self.console.print(f"[red]Failed to start recording: {e}[/]")
            self.console.print("[dim]Check microphone permissions in System Settings > Privacy & Security > Microphone[/]")
            self.ui.set_state(AppState.IDLE)
            return

        while True:
            key = self._get_next_key()
            if key == ' ':
                break
            if key.lower() == 'q':
                self._exit_requested = True
                break
            time.sleep(0.05)

        audio = self.recorder.stop_recording()
        if self._exit_requested:
            self.ui.set_state(AppState.IDLE)
            return
        
        if len(audio) == 0:
            self.console.print("[yellow]No audio recorded. Try again.[/]")
            self.ui.set_state(AppState.IDLE)
            return
        
        self.ui.set_state(AppState.TRANSCRIBING)

        try:
            result = self.transcriber.transcribe(audio)
            user_text = result.text
            t_transcribed = time.perf_counter()

            if not user_text.strip():
                self.ui.set_state(AppState.IDLE)
                return

            self.ui.set_user_message(user_text)

        except Exception as e:
            self.console.print(f"[red]Transcription error: {e}[/]")
            self.ui.set_state(AppState.IDLE)
            return

        self.ui.set_state(AppState.THINKING)
        self.ui.clear_messages()
        self.ui.set_user_message(user_text)

        # Run LLM and TTS concurrently with parallel sentence pipeline
        async def process_response():
            full_response = ""
            tts_started = False
            metrics = {
                "t_first_llm_chunk": None,
                "t_first_sentence_queued": None,
                "t_first_audio_play": None,
                "t_last_audio_play_end": None,
                "sentences_queued": 0,
                "audio_segments_played": 0,
            }
            cancel_event = threading.Event()
            
            # Configuration
            MAX_CONCURRENT_WORKERS = 4
            MAX_SENTENCE_QUEUE = 15
            
            # Sentence with sequence number
            from dataclasses import dataclass
            @dataclass
            class SentenceJob:
                seq: int
                text: str
            
            # Queues and state
            sentence_queue: asyncio.Queue[Optional[SentenceJob]] = asyncio.Queue(maxsize=MAX_SENTENCE_QUEUE)
            audio_queue: asyncio.Queue[tuple[int, np.ndarray, int] | None] = asyncio.Queue()  # (seq, audio, sr)
            
            # Sequence tracking
            next_seq = 0
            synthesis_done = False
            
            # Sentence boundaries - with and without space
            SENTENCE_END = ('. ', '! ', '? ', '.\n', '!\n', '?\n', '.', '!', '?')
            CLAUSE_END = (', ', '; ', ': ')
            MIN_CHUNK_CHARS = 28
            
            # Text buffer to accumulate across chunks
            text_buffer = ""
            last_emit_time = time.perf_counter()
            MAX_CHUNK_CHARS = 120
            MAX_WAIT_S = 0.8
            
            def split_sentences(text: str, flush: bool = False) -> list[str]:
                """Split text into sentences. If flush=True, returns any remaining text."""
                nonlocal text_buffer, last_emit_time
                sentences = []
                text_buffer += text
                
                while text_buffer:
                    # Check for sentence end (with space first, then without)
                    found_end = None
                    for punct in SENTENCE_END:
                        if punct in text_buffer:
                            idx = text_buffer.index(punct) + len(punct)
                            sentence = text_buffer[:idx]
                            text_buffer = text_buffer[idx:]
                            if sentence.strip():
                                sentences.append(sentence.strip())
                                last_emit_time = time.perf_counter()
                            found_end = punct
                            break
                    
                    if found_end:
                        continue
                    
                    if len(text_buffer) >= MIN_CHUNK_CHARS:
                        # Check for softer boundaries for long chunks only
                        for punct in CLAUSE_END:
                            if punct in text_buffer:
                                idx = text_buffer.index(punct) + len(punct)
                                clause = text_buffer[:idx]
                                if len(clause.strip()) >= MIN_CHUNK_CHARS:
                                    text_buffer = text_buffer[idx:]
                                    sentences.append(clause.strip())
                                    last_emit_time = time.perf_counter()
                                    break
                        else:
                            if flush and text_buffer.strip():
                                sentences.append(text_buffer.strip())
                                text_buffer = ""
                                last_emit_time = time.perf_counter()
                                break

                            # Fallback: if no punctuation arrives, split by length/time
                            elapsed = time.perf_counter() - last_emit_time
                            if len(text_buffer) >= MAX_CHUNK_CHARS or (
                                elapsed >= MAX_WAIT_S and len(text_buffer) >= MIN_CHUNK_CHARS
                            ):
                                cut = text_buffer.rfind(" ", 0, MAX_CHUNK_CHARS)
                                if cut < MIN_CHUNK_CHARS:
                                    cut = min(len(text_buffer), MAX_CHUNK_CHARS)
                                chunk = text_buffer[:cut]
                                text_buffer = text_buffer[cut:].lstrip()
                                if chunk.strip():
                                    sentences.append(chunk.strip())
                                    last_emit_time = time.perf_counter()
                                continue
                            break
                    else:
                        if flush and text_buffer.strip():
                            sentences.append(text_buffer.strip())
                            text_buffer = ""
                            last_emit_time = time.perf_counter()
                            break

                        # Fallback: if no punctuation arrives, split by length/time
                        elapsed = time.perf_counter() - last_emit_time
                        if len(text_buffer) >= MAX_CHUNK_CHARS or (
                            elapsed >= MAX_WAIT_S and len(text_buffer) >= MIN_CHUNK_CHARS
                        ):
                            cut = text_buffer.rfind(" ", 0, MAX_CHUNK_CHARS)
                            if cut < MIN_CHUNK_CHARS:
                                cut = min(len(text_buffer), MAX_CHUNK_CHARS)
                            chunk = text_buffer[:cut]
                            text_buffer = text_buffer[cut:].lstrip()
                            if chunk.strip():
                                sentences.append(chunk.strip())
                                last_emit_time = time.perf_counter()
                            continue
                        break
                
                return sentences
            
            def clean_text_for_speech(text: str) -> str:
                """Remove markdown/formatting characters."""
                import re
                text = re.sub(r'\*+', '', text)
                text = re.sub(r'_+', '', text)
                text = re.sub(r'`+', '', text)
                text = re.sub(r'#+', '', text)
                text = re.sub(r'>+', '', text)
                text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            
            async def synthesis_worker():
                """Simple worker: get sentence, synthesize, put to audio queue."""
                nonlocal synthesis_done
                loop = asyncio.get_event_loop()
                
                while True:
                    if cancel_event.is_set():
                        break
                    try:
                        job = await sentence_queue.get()
                        
                        if job is None:
                            break
                        
                        cleaned = clean_text_for_speech(job.text)
                        if not cleaned:
                            continue
                        if cancel_event.is_set():
                            continue
                        
                        try:
                            if hasattr(self.synthesizer, 'synthesize_stream'):
                                audio_chunks = []
                                async for chunk, sr in self.synthesizer.synthesize_stream(cleaned):
                                    if cancel_event.is_set():
                                        break
                                    audio_chunks.append(chunk)
                                if audio_chunks:
                                    audio = np.concatenate(audio_chunks)
                                    if not cancel_event.is_set():
                                        await audio_queue.put((job.seq, audio, self.synthesizer.sample_rate))
                            else:
                                audio = await loop.run_in_executor(None, self.synthesizer.synthesize, cleaned)
                                if not cancel_event.is_set():
                                    await audio_queue.put((job.seq, audio, self.synthesizer.sample_rate))
                        except:
                            pass
                            
                    except Exception:
                        if synthesis_done:
                            break
            
            async def playback_worker():
                """Play audio strictly in sentence order."""
                expected_seq = 0
                pending_audio: dict[int, tuple[np.ndarray, int]] = {}
                while True:
                    if cancel_event.is_set():
                        break
                    try:
                        item = await audio_queue.get()
                        if item is None:
                            break
                        seq, audio, sr = item
                        pending_audio[seq] = (audio, sr)
                        while expected_seq in pending_audio:
                            play_audio, play_sr = pending_audio.pop(expected_seq)
                            if metrics["t_first_audio_play"] is None:
                                metrics["t_first_audio_play"] = time.perf_counter()
                            await self.player.play_direct(play_audio, play_sr)
                            metrics["t_last_audio_play_end"] = time.perf_counter()
                            metrics["audio_segments_played"] += 1
                            expected_seq += 1
                    except Exception:
                        if synthesis_done:
                            break
            
            async def send_sentence(text: str):
                """Send sentence to queue with timeout."""
                nonlocal next_seq
                if cancel_event.is_set():
                    return
                try:
                    await asyncio.wait_for(
                        sentence_queue.put(SentenceJob(seq=next_seq, text=text)),
                        timeout=1.0
                    )
                    if metrics["t_first_sentence_queued"] is None:
                        metrics["t_first_sentence_queued"] = time.perf_counter()
                    next_seq += 1
                    metrics["sentences_queued"] += 1
                except asyncio.TimeoutError:
                    pass

            def handle_live_keys() -> None:
                """Handle queued keys during processing (cancel/stop/quit)."""
                for key in self._drain_keys():
                    k = key.lower()
                    if k in ("c", "s"):
                        cancel_event.set()
                        try:
                            self.player.stop()
                        except Exception:
                            pass
                    elif k == "q":
                        cancel_event.set()
                        self._exit_requested = True
                        try:
                            self.player.stop()
                        except Exception:
                            pass
            
            # Start workers
            try:
                # Warm up TTS once per app lifetime to reduce first-turn latency
                if not self._tts_warmed_up:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.synthesizer.synthesize, "hello")
                    self._tts_warmed_up = True
                
                playback_task = None
                
                # Start synthesis workers and playback worker together
                workers = [asyncio.create_task(synthesis_worker()) for _ in range(MAX_CONCURRENT_WORKERS)]
                playback_task = asyncio.create_task(playback_worker())
                
                # Yield to event loop to let playback worker start BEFORE sending sentences
                await asyncio.sleep(0.1)
                
                for chunk in self.llm.generate_stream(user_text):
                    handle_live_keys()
                    if cancel_event.is_set():
                        break
                    if chunk.content:
                        if metrics["t_first_llm_chunk"] is None:
                            metrics["t_first_llm_chunk"] = time.perf_counter()
                        full_response += chunk.content
                        self.ui.append_ai_response(chunk.content)
                        
                        # Split into sentences
                        sentences = split_sentences(chunk.content)
                        
                        # Mark as speaking when we have sentences
                        if sentences and not tts_started:
                            tts_started = True
                            self.ui.set_state(AppState.SPEAKING)
                        
                        # Send sentences to queue (with backpressure)
                        for sentence in sentences:
                            await send_sentence(sentence)
                    
                    if chunk.is_done:
                        # Flush remaining text in buffer
                        remaining_sentences = split_sentences("", flush=True)
                        
                        # Mark as speaking if we have any sentences
                        if remaining_sentences and not tts_started:
                            tts_started = True
                            self.ui.set_state(AppState.SPEAKING)
                        
                        # Send remaining sentences to queue
                        for sentence in remaining_sentences:
                            await send_sentence(sentence)
                        
                        # Signal workers we're done
                        synthesis_done = True
                        
                        # Send shutdown to workers
                        for _ in range(MAX_CONCURRENT_WORKERS):
                            await sentence_queue.put(None)
                        
                        # Wait for workers, then stop playback worker cleanly
                        await asyncio.gather(*workers, return_exceptions=True)
                        await audio_queue.put(None)
                        await playback_task
                        return metrics
                        
                        break

                # If cancelled mid-stream, drain and stop workers quickly
                if cancel_event.is_set():
                    synthesis_done = True
                    while not sentence_queue.empty():
                        try:
                            sentence_queue.get_nowait()
                        except Exception:
                            break
                    for _ in range(MAX_CONCURRENT_WORKERS):
                        await sentence_queue.put(None)
                    await asyncio.gather(*workers, return_exceptions=True)
                    await audio_queue.put(None)
                    await playback_task
                    return metrics
                return metrics
                        
            except Exception as e:
                self.console.print(f"[red]TTS error: {e}[/]")
                self.ui.set_state(AppState.IDLE)
                return metrics

        try:
            metrics = asyncio.run(process_response())
        except Exception as e:
            self.console.print(f"[red]LLM error: {e}[/]")
            self.ui.set_state(AppState.IDLE)
            return

        self.ui.set_state(AppState.IDLE)
        t_done = time.perf_counter()

        def rel_ms(ts: float | None) -> str:
            if ts is None:
                return "n/a"
            return f"{(ts - turn_t0) * 1000:.0f}ms"

        self.console.print(
            "[dim]Latency "
            f"(transcribe:{rel_ms(t_transcribed)} | "
            f"first_token:{rel_ms(metrics.get('t_first_llm_chunk'))} | "
            f"first_sentence:{rel_ms(metrics.get('t_first_sentence_queued'))} | "
            f"first_audio:{rel_ms(metrics.get('t_first_audio_play'))} | "
            f"done:{(t_done - turn_t0) * 1000:.0f}ms | "
            f"sentences:{metrics.get('sentences_queued', 0)} | "
            f"segments:{metrics.get('audio_segments_played', 0)})[/]"
        )

        # Rolling stats (p50/p95) over recent turns
        self._latency_history.append({
            "first_token": (metrics.get("t_first_llm_chunk") - turn_t0) * 1000
            if metrics.get("t_first_llm_chunk") else None,
            "first_audio": (metrics.get("t_first_audio_play") - turn_t0) * 1000
            if metrics.get("t_first_audio_play") else None,
            "done": (t_done - turn_t0) * 1000,
        })

        def percentile(vals: list[float], p: float) -> float | None:
            if not vals:
                return None
            vals = sorted(vals)
            k = int((p / 100) * (len(vals) - 1))
            return vals[k]

        def summarize(name: str) -> str:
            values = [v for v in (d.get(name) for d in self._latency_history) if v is not None]
            p50 = percentile(values, 50)
            p95 = percentile(values, 95)
            if p50 is None or p95 is None:
                return f"{name}: n/a"
            return f"{name}: {p50:.0f}/{p95:.0f}ms"

        self.console.print(
            f"[dim]Rolling (N={len(self._latency_history)}) "
            f"{summarize('first_token')} | {summarize('first_audio')} | {summarize('done')}[/]"
        )

        if self._exit_requested:
            return


def main() -> None:
    """Entry point."""
    try:
        app = VoiceTryApp()
        app.run()
    except ValueError as e:
        console = Console()
        console.print(f"[red]Error: {e}[/]")
        console.print("[dim]Make sure DEEPSEEK_API_KEY is set in .env file[/]")
        sys.exit(1)
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
