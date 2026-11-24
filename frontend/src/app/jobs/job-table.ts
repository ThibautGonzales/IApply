import { DatePipe } from '@angular/common';
import { Component, inject, input } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer } from './jobs.service';

/** Table of job offers, each title linking to the original posting. */
@Component({
  imports: [DatePipe],
  selector: 'app-job-table',
  styleUrl: './job-table.css',
  templateUrl: './job-table.html',
})
export class JobTable {
  protected readonly i18n = inject(I18nService);

  readonly jobs = input.required<JobOffer[]>();
}
