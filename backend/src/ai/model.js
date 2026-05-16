// ════════════════════════════════════════════════════════
//  AI MODEL ADAPTER — Supports OpenAI & Gemini
// ════════════════════════════════════════════════════════

import config from '../config/index.js';
import axios from 'axios';

class AIModel {
  constructor() {
    this.provider = config.ai.provider;
    this.model = this.provider === 'openai' ? config.ai.openai.model : null;
    this._clientReady = this._initClient();
  }

  async _initClient() {
    if (this.provider === 'openai') {
      const { default: OpenAI } = await import('openai');
      this.client = new OpenAI({
        apiKey: config.ai.openai.apiKey,
        baseURL: config.ai.openai.baseUrl,
      });
    }
  }

  async complete(prompt, systemPrompt = '', conversationHistory = []) {
    await this._clientReady;
    if (this.provider === 'openai') {
      return this._openaiComplete(prompt, systemPrompt, conversationHistory);
    } else {
      return this._geminiComplete(prompt, systemPrompt, conversationHistory);
    }
  }

  async _openaiComplete(prompt, systemPrompt, history) {
    const messages = [];
    if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
    history.slice(-10).forEach(msg => {
      messages.push({ role: msg.role || 'user', content: msg.content });
    });
    messages.push({ role: 'user', content: prompt });
    const response = await this.client.chat.completions.create({
      model: this.model,
      messages,
      temperature: 0.7,
      max_tokens: 2000,
    });
    return response.choices[0]?.message?.content || '';
  }

  async _geminiComplete(prompt, systemPrompt, history) {
    const contents = [];
    history.slice(-10).forEach(msg => {
      contents.push({
        role: msg.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: msg.content }],
      });
    });
    const payload = {
      contents,
      systemInstruction: systemPrompt ? { parts: [{ text: systemPrompt }] } : undefined,
      generationConfig: { temperature: 0.7, maxOutputTokens: 2000 },
    };
    if (contents.length === 0) {
      payload.contents = [{ role: 'user', parts: [{ text: prompt }] }];
    } else {
      payload.contents.push({ role: 'user', parts: [{ text: prompt }] });
    }
    const url = `${config.ai.gemini.baseUrl}/models/${config.ai.gemini.model}:generateContent?key=${config.ai.gemini.apiKey}`;
    const response = await axios.post(url, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
    });
    return response.data?.candidates?.[0]?.content?.parts?.[0]?.text || '';
  }

  async analyzeImage(imageBase64, prompt) {
    await this._clientReady;
    if (this.provider === 'openai') {
      const response = await this.client.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${imageBase64}` } },
          ],
        }],
        max_tokens: 1000,
      });
      return response.choices[0]?.message?.content || '';
    }
    return '';
  }

  async transcribe(audioBase64, mimeType = 'audio/ogg') {
    await this._clientReady;
    if (this.provider === 'openai') {
      const response = await this.client.audio.transcriptions.create({
        model: 'whisper-1',
        file: Buffer.from(audioBase64, 'base64'),
        file_name: 'audio.ogg',
        response_format: 'text',
      });
      return response.text || '';
    }
    return '';
  }
}

let instance = null;
export function getAIModel() {
  if (!instance) instance = new AIModel();
  return instance;
}

export default AIModel;
