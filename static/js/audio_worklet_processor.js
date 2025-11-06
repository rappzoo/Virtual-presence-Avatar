class PCM16WriterProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super(options);
    this.channels = 1;
  }

  process(inputs) {
    if (!inputs || inputs.length === 0) {
      return true;
    }
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }
    const channelData = input[0]; // mono
    if (!channelData) {
      return true;
    }

    // Convert Float32 [-1,1] to PCM16
    const pcm16 = new Int16Array(channelData.length);
    for (let i = 0; i < channelData.length; i++) {
      let s = channelData[i];
      s = Math.max(-1, Math.min(1, s));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // Post to main thread as transferable
    const uint8 = new Uint8Array(pcm16.buffer);
    this.port.postMessage(uint8, [uint8.buffer]);
    return true;
  }
}

registerProcessor('pcm16-writer', PCM16WriterProcessor);


