class AudioProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input.length > 0) {
            const channelData = input[0];
            // Convert Float32Array to Int16Array (PCM)
            const int16Data = new Int16Array(channelData.length);
            for (let i = 0; i < channelData.length; i++) {
                const s = Math.max(-1, Math.min(1, channelData[i]));
                int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            // Send to main thread
            this.port.postMessage(int16Data.buffer, [int16Data.buffer]);
        }
        return true; // Keep processor alive
    }
}

registerProcessor('audio-processor', AudioProcessor);
