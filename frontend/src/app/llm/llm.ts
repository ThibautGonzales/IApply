import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { I18nService } from '../core/i18n/i18n.service';
import { TranslationKey } from '../core/i18n/translations';
import { LlmService, LlmSettings, LlmSettingsChange } from './llm.service';

/** A line under the form: a translated text, plus the provider's raw error when there is one. */
interface Feedback {
  error: boolean;
  key: TranslationKey;
  detail?: string;
}

/** LLM page: the provider, the model and the API key used to score the offers. */
@Component({
  selector: 'app-llm',
  styleUrl: './llm.css',
  templateUrl: './llm.html',
})
export class Llm implements OnInit {
  private readonly llmService = inject(LlmService);
  protected readonly i18n = inject(I18nService);

  protected readonly settings = signal<LlmSettings | null>(null);
  // Form fields. The key field always starts empty: the backend never sends the key back.
  protected readonly provider = signal('');
  protected readonly model = signal('');
  protected readonly apiKey = signal('');
  protected readonly busy = signal(false);
  protected readonly feedback = signal<Feedback | null>(null);

  /** Shown in the empty model field: the default model of the selected provider. */
  protected readonly defaultModel = computed(
    () => this.settings()?.providers.find((p) => p.id === this.provider())?.default_model ?? '',
  );

  ngOnInit(): void {
    this.llmService.getSettings().subscribe((settings) => this.show(settings));
  }

  protected onProviderChange(provider: string): void {
    this.provider.set(provider);
    this.model.set(''); // a model name of one provider means nothing to another
  }

  protected save(): void {
    const change: LlmSettingsChange = { model: this.model() };
    if (this.provider()) {
      change.provider = this.provider();
    }
    if (this.apiKey()) {
      change.api_key = this.apiKey();
    }
    this.run(this.llmService.saveSettings(change), (settings) => {
      this.show(settings);
      this.feedback.set({ error: false, key: 'llm.saved' });
    });
  }

  protected test(): void {
    this.run(this.llmService.test(), () => this.feedback.set({ error: false, key: 'llm.testOk' }));
  }

  /** Shared by both buttons: disables them during the call and shows the error if it fails. */
  private run<T>(call: Observable<T>, next: (value: T) => void): void {
    this.busy.set(true);
    this.feedback.set(null);
    call.subscribe({
      next: (value) => {
        this.busy.set(false);
        next(value);
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.feedback.set({ error: true, key: 'llm.failed', detail: error.error?.detail });
      },
    });
  }

  private show(settings: LlmSettings): void {
    this.settings.set(settings);
    this.provider.set(settings.provider ?? '');
    // The field stays empty when the default model is used, so the placeholder shows it.
    const isDefault = settings.providers.some(
      (p) => p.id === settings.provider && p.default_model === settings.model,
    );
    this.model.set(isDefault ? '' : (settings.model ?? ''));
    this.apiKey.set('');
  }
}
