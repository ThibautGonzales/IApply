import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer } from '../jobs/jobs.service';
import { OfferDetails } from '../jobs/offer-details';
import {
  APPLICATION_STATUSES,
  Application,
  ApplicationStatus,
  ApplicationsService,
} from './applications.service';

/** Tracking page: the offers the user applied to, with their status. */
@Component({
  imports: [DatePipe, OfferDetails],
  selector: 'app-applications',
  templateUrl: './applications.html',
})
export class Applications implements OnInit {
  private readonly applicationsService = inject(ApplicationsService);
  protected readonly i18n = inject(I18nService);

  protected readonly statuses = APPLICATION_STATUSES;
  protected readonly applications = signal<Application[]>([]);
  // The application whose offer details are shown under its row, if any.
  protected readonly openedId = signal<number | null>(null);

  ngOnInit(): void {
    this.applicationsService
      .getApplications()
      .subscribe((applications) => this.applications.set(applications));
  }

  protected changeStatus(application: Application, status: string): void {
    this.applicationsService
      .changeStatus(application.id, status as ApplicationStatus)
      .subscribe((updated) => this.replace(updated));
  }

  protected recordNews(application: Application): void {
    this.applicationsService
      .recordNews(application.id)
      .subscribe((updated) => this.replace(updated));
  }

  protected toggleOffer(application: Application): void {
    this.openedId.update((id) => (id === application.id ? null : application.id));
  }

  protected replaceJob(application: Application, job: JobOffer): void {
    this.replace({ ...application, job });
  }

  // The API returns the updated application: only its row changes, no reload.
  private replace(updated: Application): void {
    this.applications.update((applications) =>
      applications.map((application) => (application.id === updated.id ? updated : application)),
    );
  }
}
