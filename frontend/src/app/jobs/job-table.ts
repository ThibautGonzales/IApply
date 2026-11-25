import { DatePipe } from '@angular/common';
import { Component, inject, input, output } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer } from './jobs.service';

/** Table of job offers, each title linking to the original posting, with the actions on each offer. */
@Component({
  imports: [DatePipe],
  selector: 'app-job-table',
  templateUrl: './job-table.html',
})
export class JobTable {
  protected readonly i18n = inject(I18nService);

  readonly jobs = input.required<JobOffer[]>();
  // The table only reports the click: the parent calls the API and updates the list.
  readonly hide = output<JobOffer>();
  readonly apply = output<JobOffer>();
}
