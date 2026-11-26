import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** A supported LLM provider, as listed by the backend `PROVIDERS`. */
export interface LlmProvider {
  id: string;
  label: string;
  default_model: string;
}

/** The LLM settings, as returned by the backend `LlmSettingsView`. The key never comes back. */
export interface LlmSettings {
  provider: string | null;
  model: string | null;
  api_key_hint: string | null;
  providers: LlmProvider[];
}

/** What the page sends: a missing field is left unchanged by the backend. */
export interface LlmSettingsChange {
  provider?: string;
  model?: string;
  api_key?: string;
}

/** Talks to the backend `/llm` routes. */
@Injectable({ providedIn: 'root' })
export class LlmService {
  private readonly http = inject(HttpClient);

  getSettings(): Observable<LlmSettings> {
    return this.http.get<LlmSettings>('/api/llm');
  }

  saveSettings(change: LlmSettingsChange): Observable<LlmSettings> {
    return this.http.put<LlmSettings>('/api/llm', change);
  }

  test(): Observable<unknown> {
    return this.http.post('/api/llm/test', {});
  }
}
