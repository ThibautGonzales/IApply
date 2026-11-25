import { DatePipe } from '@angular/common';
import { Component, inject, input, output, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer } from './jobs.service';
import { OfferDetails } from './offer-details';

/** Table of job offers, each title linking to the original posting, with the actions on each offer. */
@Component({
  imports: [DatePipe, OfferDetails],
  selector: 'app-job-table',
  templateUrl: './job-table.html',
})
export class JobTable {
  protected readonly i18n = inject(I18nService);

  readonly jobs = input.required<JobOffer[]>();
  // The table only reports the click: the parent calls the API and updates the list.
  readonly hide = output<JobOffer>();
  readonly apply = output<JobOffer>();
  readonly saved = output<JobOffer>(); // the offer text was saved

  // The offer whose details are shown under its row, if any.
  protected readonly openedId = signal<number | null>(null);

  protected toggleOffer(job: JobOffer): void {
    this.openedId.update((id) => (id === job.id ? null : job.id));
  }
}
