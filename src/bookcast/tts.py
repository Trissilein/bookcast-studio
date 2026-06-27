from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TtsVoice:
    id: str
    label: str
    locale: str | None = None


class TtsProvider:
    id = "base"

    def health(self) -> bool:
        raise NotImplementedError

    def list_voices(self) -> list[TtsVoice]:
        raise NotImplementedError

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        raise NotImplementedError


class WindowsSapiProvider(TtsProvider):
    id = "windows_sapi"

    def __init__(self, powershell: str = "powershell") -> None:
        self.powershell = powershell

    def health(self) -> bool:
        try:
            subprocess.run(
                [self.powershell, "-NoProfile", "-NonInteractive", "-Command", "Add-Type -AssemblyName System.Speech"],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return False
        return True

    def list_voices(self) -> list[TtsVoice]:
        script = """
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.GetInstalledVoices() | ForEach-Object {
  $i = $_.VoiceInfo
  "$($i.Name)`t$($i.Culture)"
}
"""
        proc = subprocess.run(
            [self.powershell, "-NoProfile", "-NonInteractive", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return []
        voices: list[TtsVoice] = []
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if parts and parts[0]:
                voices.append(TtsVoice(id=parts[0], label=parts[0], locale=parts[1] if len(parts) > 1 else None))
        return voices

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        output_wav = Path(output_wav)
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["BOOKCAST_TTS_OUT"] = str(output_wav)
        env["BOOKCAST_TTS_RATE"] = str(rate)
        if voice:
            env["BOOKCAST_TTS_VOICE"] = voice
        script = r"""
Add-Type -AssemblyName System.Speech
$text = [Console]::In.ReadToEnd()
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($env:BOOKCAST_TTS_VOICE) { $s.SelectVoice($env:BOOKCAST_TTS_VOICE) }
$s.Rate = [int]$env:BOOKCAST_TTS_RATE
$s.SetOutputToWaveFile($env:BOOKCAST_TTS_OUT)
$s.Speak($text)
$s.Dispose()
"""
        proc = subprocess.run(
            [self.powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
            input=text,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"Windows SAPI synthesis failed: {detail}")
        if not output_wav.exists() or output_wav.stat().st_size == 0:
            raise RuntimeError(f"Windows SAPI produced no audio: {output_wav}")


class AudioCppProvider(TtsProvider):
    id = "audio_cpp"

    def __init__(
        self,
        executable: str,
        *,
        model: str,
        backend: str = "cpu",
        family: str | None = None,
    ) -> None:
        self.executable = executable
        self.model = model
        self.backend = backend
        self.family = family

    def health(self) -> bool:
        try:
            proc = subprocess.run(
                [self.executable, "--help"],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return False
        return proc.returncode in {0, 1}

    def list_voices(self) -> list[TtsVoice]:
        return [TtsVoice(id="default", label="audio.cpp default")]

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        if not self.model:
            raise RuntimeError("audio.cpp model path/name is required")
        output_wav = Path(output_wav)
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        args = [
            self.executable,
            "--task",
            "tts",
            "--model",
            self.model,
            "--backend",
            self.backend,
            "--text",
            text,
            "--out",
            str(output_wav),
        ]
        if self.family:
            args.extend(["--family", self.family])
        if voice:
            args.extend(["--voice", voice])
        if rate:
            args.extend(["--rate", str(rate)])
        proc = subprocess.run(args, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"audio.cpp synthesis failed: {detail}")
        if not output_wav.exists() or output_wav.stat().st_size == 0:
            raise RuntimeError(f"audio.cpp produced no audio: {output_wav}")


def play_wav(path: Path, powershell: str = "powershell") -> None:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    script = f"""
$player = New-Object System.Media.SoundPlayer('{str(path).replace("'", "''")}')
$player.PlaySync()
"""
    proc = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"WAV playback failed: {detail}")
