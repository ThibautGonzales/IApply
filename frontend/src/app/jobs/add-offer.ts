import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, output, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { I18nService } from '../core/i18n/i18n.service';
import { ExtractedOffer, JobOffer, JobsService } from './jobs.service';

/**
 * "Add an offer" on the offers page: the user pastes the text and the link of an offer found
 * elsewhere, the LLM fills in the fields, the user checks them and saves the offer.
 * The offers page shows it when "Add an offer" is clicked in its header.
 */
@Component({
  selector: 'app-add-offer',
  styleUrl: './add-offer.css',
  templateUrl: './add-offer.html',
})
export class AddOffer {
  private readonly jobsService = inject(JobsService);
  protected readonly i18n = inject(I18nService);

  // Sends the saved offer so the offers page can put it in its list (and close the form).
  readonly added = output<JobOffer>();
  // "Cancel": the offers page closes the form.
  readonly closed = output<void>();

  protected readonly text = signal('');
  protected readonly url = signal('');
  // The fields read by the LLM: the form to check appears once they are there.
  protected readonly extracted = signal<ExtractedOffer | null>(null);
  protected readonly busy = signal(false);
  // null: no error. Otherwise the API's own message (the provider's error, a duplicate link...),
  // shown as it is; empty when the API gave none.
  protected readonly error = signal<string | null>(null);

  protected read(): void {
    this.call(this.jobsService.extractOffer(this.text()), (fields) => this.extracted.set(fields));
  }

  protected save(fields: ExtractedOffer): void {
    const url = this.url().trim();
    if (!url || !fields.title) {
      this.error.set(this.i18n.t('add.missing'));
      return;
    }
    const offer = { ...fields, url, description: this.text() };
    this.call(this.jobsService.addOffer(offer), (saved) => {
      this.added.emit(saved);
    });
  }

  protected close(): void {
    this.closed.emit();
  }

  /** Shared by both buttons: disables them during the call and shows the error if it fails. */
  private call<T>(request: Observable<T>, done: (value: T) => void): void {
    this.busy.set(true);
    this.error.set(null);
    request.subscribe({
      next: (value) => {
        this.busy.set(false);
        done(value);
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        // A refused field (422) gives a list, not a text: only a text is worth showing.
        const detail = error.error?.detail;
        this.error.set(typeof detail === 'string' ? detail : '');
      },
    });
  }
}
