import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { TranslationKey } from '../core/i18n/translations';
import { AddOffer } from './add-offer';
import { JobTable } from './job-table';
import { CollectionResult, JobOffer, JobsService } from './jobs.service';

/** Collect button and the saved job offers, on-site and remote apart. */
@Component({
  imports: [AddOffer, JobTable],
  selector: 'app-jobs',
  templateUrl: './jobs.html',
})
export class Jobs implements OnInit {
  private readonly jobsService = inject(JobsService);
  protected readonly i18n = inject(I18nService);

  protected readonly jobs = signal<JobOffer[]>([]);
  protected readonly onSiteJobs = computed(() => this.jobs().filter((job) => !job.remote));
  protected readonly remoteJobs = computed(() => this.jobs().filter((job) => job.remote));
  protected readonly collecting = signal(false);
  protected readonly result = signal<CollectionResult | null>(null);
  protected readonly failed = signal(false);

  // Built from the raw result, so the message is translated again when the language changes.
  protected readonly message = computed(() => {
    const t = (key: TranslationKey) => this.i18n.t(key);
    const result = this.result();
    if (this.failed()) {
      return t('collect.failed');
    }
    if (!result) {
      return '';
    }
    const errors = result.errors.length
      ? ` ${t('collect.errors')} ${result.errors.join(', ')}`
      : '';
    const scoring = result.scoring_error
      ? ` ${t('collect.notScored')} ${result.scoring_error}`
      : ` ${result.scored} ${t('collect.scored')}`;
    return `${result.added} ${t('collect.newOffers')} (${result.fetched} ${t('collect.found')}).${errors}${scoring}`;
  });

  ngOnInit(): void {
    this.loadJobs();
  }

  protected collect(): void {
    this.collecting.set(true);
    this.result.set(null);
    this.failed.set(false);
    this.jobsService.collect().subscribe({
      next: (result) => {
        this.result.set(result);
        this.collecting.set(false);
        this.loadJobs();
      },
      error: () => {
        this.failed.set(true);
        this.collecting.set(false);
        // The backend may have saved offers (and scores) before the error: show them.
        this.loadJobs();
      },
    });
  }

  protected hide(job: JobOffer): void {
    this.jobsService.hide(job.id).subscribe(() => this.removeFromList(job));
  }

  protected apply(job: JobOffer): void {
    this.jobsService.apply(job.id).subscribe(() => this.removeFromList(job));
  }

  // An offer added by hand is never scored: it goes first, as the list sorts unscored offers first.
  protected add(offer: JobOffer): void {
    this.jobs.update((jobs) => [offer, ...jobs]);
  }

  // The saved offer comes back from the API: only its row changes.
  protected replace(updated: JobOffer): void {
    this.jobs.update((jobs) => jobs.map((job) => (job.id === updated.id ? updated : job)));
  }

  // Removed locally once the API has answered: no need to reload the whole list.
  private removeFromList(job: JobOffer): void {
    this.jobs.update((jobs) => jobs.filter((other) => other.id !== job.id));
  }

  private loadJobs(): void {
    this.jobsService.getJobs().subscribe((jobs) => this.jobs.set(jobs));
  }
}
