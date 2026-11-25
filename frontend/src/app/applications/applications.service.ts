import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { JobOffer } from '../jobs/jobs.service';

/** Statuses of an application (backend `ApplicationStatus`), in the order of the status list. */
export const APPLICATION_STATUSES = [
  'waiting',
  'interview',
  'rejected',
  'accepted',
  'closed',
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

/** An application with its offer, as returned by the backend `ApplicationWithJob`. */
export interface Application {
  id: number;
  status: ApplicationStatus;
  applied_at: string;
  last_news_at: string;
  job: JobOffer;
}

/** Talks to the backend `/applications` routes. */
@Injectable({ providedIn: 'root' })
export class ApplicationsService {
  private readonly http = inject(HttpClient);

  getApplications(): Observable<Application[]> {
    return this.http.get<Application[]>('/api/applications');
  }

  changeStatus(applicationId: number, status: ApplicationStatus): Observable<Application> {
    return this.http.put<Application>(`/api/applications/${applicationId}/status`, { status });
  }

  recordNews(applicationId: number): Observable<Application> {
    return this.http.post<Application>(`/api/applications/${applicationId}/news`, null);
  }
}
