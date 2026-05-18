"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { voiceApi } from "./api"

/**
 * useVoiceRecorder
 *
 * 录音并通过后端 STT 转写;不可用时返回 error。
 */
export function useVoiceRecorder() {
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = useCallback(async (): Promise<void> => {
    setError(null)
    if (typeof window === "undefined" || !navigator.mediaDevices) {
      setError("浏览器不支持录音")
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.start()
      mediaRef.current = recorder
      setRecording(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法启动麦克风")
    }
  }, [])

  const stopAndTranscribe = useCallback(async (): Promise<string | null> => {
    const recorder = mediaRef.current
    if (!recorder) return null
    return new Promise<string | null>((resolve) => {
      recorder.onstop = async () => {
        setRecording(false)
        recorder.stream.getTracks().forEach((t) => t.stop())
        if (chunksRef.current.length === 0) {
          resolve(null)
          return
        }
        const blob = new Blob(chunksRef.current, { type: "audio/webm" })
        try {
          setTranscribing(true)
          const res = await voiceApi.transcribe(blob)
          resolve(res.text ?? "")
        } catch (err) {
          setError(err instanceof Error ? err.message : "转写失败")
          resolve(null)
        } finally {
          setTranscribing(false)
          mediaRef.current = null
        }
      }
      recorder.stop()
    })
  }, [])

  const cancel = useCallback(() => {
    const recorder = mediaRef.current
    if (recorder && recorder.state !== "inactive") {
      recorder.stop()
      recorder.stream.getTracks().forEach((t) => t.stop())
    }
    mediaRef.current = null
    chunksRef.current = []
    setRecording(false)
  }, [])

  useEffect(() => cancel, [cancel])

  return { recording, transcribing, error, start, stopAndTranscribe, cancel }
}

/**
 * 播放 TTS;优先调用后端 OpenAI TTS,失败时降级 Web SpeechSynthesis。
 */
export async function speak(text: string): Promise<void> {
  if (!text?.trim()) return
  try {
    const blob = await voiceApi.synthesize(text)
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => URL.revokeObjectURL(url)
    await audio.play()
    return
  } catch {
    /* fallback */
  }
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = "zh-CN"
    utter.rate = 1.0
    window.speechSynthesis.speak(utter)
  }
}

export function stopSpeak() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel()
  }
}
