import React, { useState, useEffect, useRef } from 'react';
import TextDisplay from './TextDisplay';
import AudioControls from './AudioControls';
import LoadingIndicator from './LoadingIndicator';

const AudioDisplay = ({ items }) => {
  // State Variables
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTextVisible, setIsTextVisible] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // Refs
  const audioRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameIdRef = useRef(null);
  const currentItemIndexRef = useRef(currentItemIndex);

  // SiriWave Configurations
  const [siriWaveConfigs, setSiriWaveConfigs] = useState({
    theme: 'ios9',
    speed: 0,
    amplitude: 0,
    frequency: 0,
    cover: true,
    color: '#FAEE1C',
    width: 200,
    height: 200,
    autostart: true,
    pixelDepth: 1,
    lerpSpeed: 0.1,
  });

  // Variants for text animations
  const textContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15, // Delay between each character
      },
    },
  };

  const textChildVariants = {
    hidden: { opacity: 0, scale: 1.5 },
    visible: { opacity: 1, scale: 1 },
  };

  const messageContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,  // Delay between each character's appearance
        delayChildren: 0.2,     // Delay before starting the animation
      },
    },
  };

  const messageChild = {
    hidden: { opacity: 0, y: -10 },  // Start with opacity 0 and slightly above the position
    visible: { opacity: 1, y: 0 },   // Fade in and slide to the correct position
  };

  const download_msg = "Downloading...";
  const text =  download_msg.split("");

  // Update currentItemIndexRef whenever currentItemIndex changes
  useEffect(() => {
    currentItemIndexRef.current = currentItemIndex;
  }, [currentItemIndex]);

  // Initialize AudioContext and Audio Element on mount
  useEffect(() => {
    // Initialize AudioContext
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioContextRef.current = new AudioContext();

    // Initialize Audio Element
    audioRef.current = new Audio();

    // Initialize MediaElementSourceNode and AnalyserNode
    sourceRef.current = audioContextRef.current.createMediaElementSource(
      audioRef.current
    );
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256; // Adjust as needed

    sourceRef.current.connect(analyserRef.current);
    analyserRef.current.connect(audioContextRef.current.destination);

    // Event listener for audio ended
    const handleEnded = () => {
      if (currentItemIndexRef.current + 1 < items.length) {
        setCurrentItemIndex((prevIndex) => prevIndex + 1);
      } else {
        setCurrentItemIndex(0);
        setIsTextVisible(false);
        setIsPlaying(false);
      }
    };
    audioRef.current.addEventListener('ended', handleEnded);

    // Cleanup function
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeEventListener('ended', handleEnded);
      }
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [items.length]);

  // Update audio source when currentItemIndex changes
  useEffect(() => {
    if (audioRef.current && items[currentItemIndex]) {
      fetch(items[currentItemIndex].audioUrl)
        .then((response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.blob(); // Convert the response to a Blob
        })
        .then((blob) => {
          const blobUrl = URL.createObjectURL(blob); // Create a blob URL for the audio
          audioRef.current.src = blobUrl; // Set the audio element source to the blob URL
          audioRef.current.load();
          if (isPlaying) {
            audioRef.current.play().catch((error) => {
              console.error('Error playing audio:', error);
              setIsPlaying(false);
            });
            startAmplitudeUpdates();
          }
        })
        .catch((error) => {
          console.error('Error fetching the audio file:', error);
        });
    }
    // Reset display text
  }, [currentItemIndex, isPlaying, items]);

  // Handle play/pause when isPlaying changes
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioContextRef.current.resume().then(() => {
          audioRef.current.play().catch((error) => {
            console.error('Error playing audio:', error);
            setIsPlaying(false);
          });
          startAmplitudeUpdates();
        });
      } else {
        audioRef.current.pause();
        stopAmplitudeUpdates();
      }
    }
  }, [isPlaying]);

  // Amplitude Update Function
  const updateAmplitude = () => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteTimeDomainData(dataArray);

    // Compute amplitude based on time-domain data
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += (dataArray[i] - 128) * (dataArray[i] - 128); // Normalize and square
    }
    const rms = Math.sqrt(sum / bufferLength); // Root mean square for amplitude
    const normalizedAmplitude = rms / 128; // Normalize between 0 and 1

    // Update the SiriWave config
    setSiriWaveConfigs((prevConfigs) => ({
      ...prevConfigs,
      amplitude:
        normalizedAmplitude > 0.001
          ? normalizedAmplitude > 0.2
            ? normalizedAmplitude * 10 // Scale less for values greater than 0.2
            : normalizedAmplitude * 75 // Scale more for values between 0.001 and 0.2
          : 0,
      speed: 0.001,
      frequency: 1,
    }));

    // Continue updating in the next frame
    setTimeout(() => {
      animationFrameIdRef.current = requestAnimationFrame(updateAmplitude);
    }, 75);
  };

  // Start Amplitude Updates
  const startAmplitudeUpdates = () => {
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }
    animationFrameIdRef.current = requestAnimationFrame(updateAmplitude);
  };

  // Stop Amplitude Updates
  const stopAmplitudeUpdates = () => {
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }
    setSiriWaveConfigs((prevConfigs) => ({
      ...prevConfigs,
      amplitude: 0,
      speed: 0,
      frequency: 0,
    }));
  };

  // Play/Pause Button Handler
  const handlePlayPause = () => {
    setIsPlaying((prevIsPlaying) => {
      const newIsPlaying = !prevIsPlaying;
      if (newIsPlaying && !isTextVisible) {
        // Play button pressed for the first time
        setIsTextVisible(true);
      }
      return newIsPlaying;
    });
  };

  // Download Concatenated Audio
  const handleDownload = async () => {
    try {
      setIsDownloading(true);

      // Fetch all audio files as ArrayBuffers
      const audioBuffers = await Promise.all(
        items.map(async (item) => {
          const response = await fetch(item.audioUrl);
          if (!response.ok) throw new Error(`Failed to fetch ${item.audioUrl}`);
          return await response.arrayBuffer();
        })
      );

      // Decode audio files
      const audioContext = new (window.AudioContext ||
        window.webkitAudioContext)();
      const decodedBuffers = await Promise.all(
        audioBuffers.map((buffer) =>
          audioContext.decodeAudioData(buffer)
        )
      );

      // Calculate total length
      const totalLength = decodedBuffers.reduce(
        (sum, buffer) => sum + buffer.length,
        0
      );

      // Create a new buffer for concatenation
      const numberOfChannels = decodedBuffers[0].numberOfChannels;
      const sampleRate = decodedBuffers[0].sampleRate;
      const concatenatedBuffer = audioContext.createBuffer(
        numberOfChannels,
        totalLength,
        sampleRate
      );

      // Concatenate buffers
      let offset = 0;
      decodedBuffers.forEach((buffer) => {
        for (let channel = 0; channel < numberOfChannels; channel++) {
          concatenatedBuffer
            .getChannelData(channel)
            .set(buffer.getChannelData(channel), offset);
        }
        offset += buffer.length;
      });

      // Convert concatenated buffer to WAV Blob
      const wavBlob = bufferToWavBlob(concatenatedBuffer);

      // Create a download link
      const url = URL.createObjectURL(wavBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'concatenated_audio.wav';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading audio:', error);
      alert('Failed to download audio.');
    } finally {
      setTimeout(() => {
        setIsDownloading(false);
      }, 2000);
    }
  };

  // Helper Function: Convert AudioBuffer to WAV Blob
  const bufferToWavBlob = (buffer) => {
    const numOfChan = buffer.numberOfChannels,
      length = buffer.length * numOfChan * 2 + 44,
      bufferArray = new ArrayBuffer(length),
      view = new DataView(bufferArray),
      sampleRate = buffer.sampleRate,
      bitDepth = 16;

    let offset = 0;

    // Write WAV header
    writeString(view, offset, 'RIFF');
    offset += 4;
    view.setUint32(offset, 36 + buffer.length * numOfChan * 2, true);
    offset += 4;
    writeString(view, offset, 'WAVE');
    offset += 4;
    writeString(view, offset, 'fmt ');
    offset += 4;
    view.setUint32(offset, 16, true);
    offset += 4; // Subchunk1Size
    view.setUint16(offset, 1, true);
    offset += 2; // AudioFormat (PCM)
    view.setUint16(offset, numOfChan, true);
    offset += 2; // NumChannels
    view.setUint32(offset, sampleRate, true);
    offset += 4; // SampleRate
    view.setUint32(
      offset,
      (sampleRate * numOfChan * bitDepth) / 8,
      true
    );
    offset += 4; // ByteRate
    view.setUint16(offset, (numOfChan * bitDepth) / 8, true);
    offset += 2; // BlockAlign
    view.setUint16(offset, bitDepth, true);
    offset += 2; // BitsPerSample
    writeString(view, offset, 'data');
    offset += 4;
    view.setUint32(
      offset,
      buffer.length * numOfChan * (bitDepth / 8),
      true
    );
    offset += 4;

    // Write PCM samples
    for (let i = 0; i < buffer.length; i++) {
      for (let channel = 0; channel < numOfChan; channel++) {
        let sample = buffer.getChannelData(channel)[i];
        sample = Math.max(-1, Math.min(1, sample));
        sample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        view.setInt16(offset, sample, true);
        offset += 2;
      }
    }

    return new Blob([bufferArray], { type: 'audio/wav' });
  };

  // Helper Function: Write string to DataView
  const writeString = (view, offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  return (
    <div className="relative w-full max-w-md p-6 flex rounded-xl flex-col items-center justify-center space-y-6">
      {/* Text Display Section */}
      <TextDisplay
        isTextVisible={isTextVisible}
        items={items}
        currentItemIndex={currentItemIndex}
        textContainerVariants={textContainerVariants}
        textChildVariants={textChildVariants}
      />

      {/* Controls Section */}
      <AudioControls
        handlePlayPause={handlePlayPause}
        isPlaying={isPlaying}
        isDownloading={isDownloading}
        handleDownload={handleDownload}
        siriWaveConfigs={siriWaveConfigs}
      />

      {/* Loading Indicator */}
      <LoadingIndicator
        isDownloading={isDownloading}
        text={text}
        messageContainer={messageContainer}
        messageChild={messageChild}
      />
    </div>
  );
};

export default AudioDisplay;