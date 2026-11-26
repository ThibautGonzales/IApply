import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer, JobsService } from '../jobs/jobs.service';

/** Rejected offers page: the offers of the last week left out of the list, each one restorable. */
@Component({
  imports: [DatePipe],
  selector: 'app-rejected',
  templateUrl: './rejected.html',
})
export class Rejected implements OnInit {
  private readonly jobsService = inject(JobsService);
  protected readonly i18n = inject(I18nService);

  protected readonly jobs = signal<JobOffer[]>([]);

  ngOnInit(): void {
    this.jobsService.getRejectedJobs().subscribe((jobs) => this.jobs.set(jobs));
  }

  // Removed locally once the API has answered: the offer is back on the offers page.
  protected restore(job: JobOffer): void {
    this.jobsService
      .restore(job.id)
      .subscribe(() => this.jobs.update((jobs) => jobs.filter((other) => other.id !== job.id)));
  }
}
