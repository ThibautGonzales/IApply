import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { JobTable } from './job-table';
import { JobOffer, JobsService } from './jobs.service';

/** Collect button and the saved job offers, on-site and remote apart. */
@Component({
  imports: [JobTable],
  selector: 'app-jobs',
  templateUrl: './jobs.html',
})
export class Jobs implements OnInit {
  private readonly jobsService = inject(JobsService);

  protected readonly jobs = signal<JobOffer[]>([]);
  protected readonly onSiteJobs = computed(() => this.jobs().filter((job) => !job.remote));
  protected readonly remoteJobs = computed(() => this.jobs().filter((job) => job.remote));
  protected readonly collecting = signal(false);
  protected readonly message = signal('');

  ngOnInit(): void {
    this.loadJobs();
  }

  protected collect(): void {
    this.collecting.set(true);
    this.message.set('');
    this.jobsService.collect().subscribe({
      next: (result) => {
        const errors = result.errors.length ? ` Errors: ${result.errors.join(', ')}` : '';
        this.message.set(`${result.added} new offers (${result.fetched} found).${errors}`);
        this.collecting.set(false);
        this.loadJobs();
      },
      error: () => {
        this.message.set('Collection failed: API unreachable.');
        this.collecting.set(false);
      },
    });
  }

  private loadJobs(): void {
    this.jobsService.getJobs().subscribe((jobs) => this.jobs.set(jobs));
  }
}
