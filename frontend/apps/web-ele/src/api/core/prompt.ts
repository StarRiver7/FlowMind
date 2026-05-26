/**
 * Prompt 管理 API — Python AI 服务
 */
import { aiRequestClient } from '#/api/request';
import type { PromptTemplate } from './types';

export async function listPrompts() {
  return aiRequestClient.get<PromptTemplate[]>('/prompts');
}

export async function getPrompt(id: string) {
  return aiRequestClient.get<PromptTemplate>(`/prompts/${id}`);
}

export async function createPrompt(data: Partial<PromptTemplate>) {
  return aiRequestClient.post<PromptTemplate>('/prompts', data);
}

export async function updatePrompt(id: string, data: Partial<PromptTemplate>) {
  return aiRequestClient.put<PromptTemplate>(`/prompts/${id}`, data);
}

export async function togglePrompt(id: string, enabled: boolean) {
  return aiRequestClient.patch(`/prompts/${id}`, { enabled });
}
