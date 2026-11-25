import { Component, inject, input, output, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer, JobsService } from './jobs.service';

/**
 * What "View offer" unfolds, on the offers page and on the tracking page: the offer details,
 * its full text (pasted by the user from the original posting) and a link to that posting.
 */
@Component({
  selector: 'app-offer-details',
  styleUrl: './offer-details.css',
  templateUrl: './offer-details.html',
})
export class OfferDetails {
  private readonly jobsService = inject(JobsService);
  protected readonly i18n = inject(I18nService);

  readonly job = input.required<JobOffer>();
  // Sends the updated offer so the parent can replace it in its own list.
  readonly saved = output<JobOffer>();

  protected readonly editing = signal(false);
  protected readonly saving = signal(false);

  protected save(text: string): void {
    this.saving.set(true);
    this.jobsService.changeDescription(this.job().id, text).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.editing.set(false);
        this.saved.emit(updated);
      },
      // The text stays in the box, so the user can try again.
      error: () => this.saving.set(false),
    });
  }
}
