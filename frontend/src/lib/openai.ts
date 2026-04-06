import OpenAI from "openai";

let _openai: OpenAI | null = null;

export function getOpenAI(): OpenAI {
  if (!_openai) {
    _openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }
  return _openai;
}

export const OPENAI_MODEL = process.env.OPENAI_MODEL ?? "gpt-4o";
export const OPENAI_VISION_MODEL = process.env.OPENAI_VISION_MODEL ?? "gpt-4o";
