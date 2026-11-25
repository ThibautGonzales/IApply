import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** A saved job offer, as returned by the backend `JobOffer` model. */
export interface JobOffer {
  id: number;
  source: string;
  external_id: string;
  title: string;
  company: string | null;
  location: string | null;
  salary: string | null;
  contract_type: string | null;
  description: string | null;
  url: string;
  remote: boolean;
  published_at: string;
  collected_at: string;
}

/** Summary returned by a collection (backend `CollectionResult`). */
export interface CollectionResult {
  fetched: number;
  added: number;
  errors: string[];
}

/** Talks to the backend `/jobs` routes. */
@Injectable({ providedIn: 'root' })
export class JobsService {
  private readonly http = inject(HttpClient);

  getJobs(): Observable<JobOffer[]> {
    return this.http.get<JobOffer[]>('/api/jobs');
  }

  collect(): Observable<CollectionResult> {
    return this.http.post<CollectionResult>('/api/jobs/collect', null);
  }

  hide(jobId: number): Observable<void> {
    return this.http.post<void>(`/api/jobs/${jobId}/hide`, null);
  }

  // Returns the created application; the tracking page will use it.
  apply(jobId: number): Observable<unknown> {
    return this.http.post(`/api/jobs/${jobId}/apply`, null);
  }
}
