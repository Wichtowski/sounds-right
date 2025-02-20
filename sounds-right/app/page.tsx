"use client";

import { useEffect, useRef, useState } from "react";

const lyricsData = [
  { start: 4.48, end: 9.08, text: "I am reincarnated I was stargazin' Life goes on, I need all my babies" },
  { start: 9.08, end: 14.56, text: "gyah) Woke up lookin' for the broccoli High-key, keep a horn on me" },
  // Add the rest of the lyrics
];

export default function Karaoke() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [currentLyric, setCurrentLyric] = useState("");
  const [ballPosition, setBallPosition] = useState(0);

  useEffect(() => {
    const updateLyrics = () => {
      const currentTime = audioRef.current?.currentTime || 0;
      const activeLyric = lyricsData.find(lyric => currentTime >= lyric.start && currentTime <= lyric.end);
      setCurrentLyric(activeLyric ? activeLyric.text : "");

      if (activeLyric) {
        const progress = (currentTime - activeLyric.start) / (activeLyric.end - activeLyric.start);
        setBallPosition(progress * 100);
      }
    };

    const interval = setInterval(updateLyrics, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      <audio ref={audioRef} src="/audio/song.mp3" controls className="mb-4" />
      <div className="relative w-3/4 h-16 bg-gray-800 rounded-lg flex items-center justify-center">
        <span className="text-lg font-bold">{currentLyric}</span>
        <div className="absolute bottom-0 left-0 w-full h-1 bg-blue-500">
          <div className="h-4 w-4 bg-red-500 rounded-full transition-all" style={{ transform: `translateX(${ballPosition}%)` }} />
        </div>
      </div>
    </div>
  );
}
