/**
 * 模型管理 API
 */
import { aiRequestClient } from '#/api/request';
import type { ModelConfig } from './types';

export async function listModels() {
  return aiRequestClient.get<ModelConfig[]>('/models');
}

export async function getActiveModel() {
  return aiRequestClient.get<ModelConfig>('/models/active');
}

export async function setActiveModel(id: string) {
  return aiRequestClient.post('/models/active', { id });
}

export async function updateModel(id: string, data: Partial<ModelConfig>) {
  return aiRequestClient.put<ModelConfig>(`/models/${id}`, data);
}
