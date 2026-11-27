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
  /** Hidden by the user: the offer is on the rejected page. */
  hidden: boolean;
  /** Brought back from the rejected page: stays in the list whatever its score. */
  restored: boolean;
  /** Relevance from 0 to 100 given by the LLM, null until scored. */
  score: number | null;
  published_at: string;
  collected_at: string;
}

/** Summary returned by a collection (backend `CollectionResult`). */
export interface CollectionResult {
  fetched: number;
  added: number;
  errors: string[];
  scored: number;
  /** Why the offers could not be scored (no LLM, empty profile, provider error), if they could not. */
  scoring_error: string | null;
}

/** The fields the LLM read in a pasted offer (backend `ExtractedOffer`), checked by the user. */
export interface ExtractedOffer {
  title: string;
  company: string | null;
  location: string | null;
  contract_type: string | null;
  salary: string | null;
  remote: boolean;
}

/** What is sent to save an offer added by hand (backend `ManualOfferCreate`). */
export interface ManualOffer extends ExtractedOffer {
  url: string;
  /** The pasted text, saved as the offer description. */
  description: string;
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

  /** The offers of the last week left out of the list: hidden, or scored under the threshold. */
  getRejectedJobs(): Observable<JobOffer[]> {
    return this.http.get<JobOffer[]>('/api/jobs/rejected');
  }

  restore(jobId: number): Observable<void> {
    return this.http.post<void>(`/api/jobs/${jobId}/restore`, null);
  }

  hide(jobId: number): Observable<void> {
    return this.http.post<void>(`/api/jobs/${jobId}/hide`, null);
  }

  getJob(jobId: number): Observable<JobOffer> {
    return this.http.get<JobOffer>(`/api/jobs/${jobId}`);
  }

  changeDescription(jobId: number, description: string): Observable<JobOffer> {
    return this.http.put<JobOffer>(`/api/jobs/${jobId}/description`, { description });
  }

  /** Asks the LLM for the fields of a pasted offer. Nothing is saved. */
  extractOffer(text: string): Observable<ExtractedOffer> {
    return this.http.post<ExtractedOffer>('/api/jobs/manual/extract', { text });
  }

  /** Saves an offer added by hand. It is never scored, so it comes first in the list. */
  addOffer(offer: ManualOffer): Observable<JobOffer> {
    return this.http.post<JobOffer>('/api/jobs/manual', offer);
  }

  // Returns the created application; the tracking page will use it.
  apply(jobId: number): Observable<unknown> {
    return this.http.post(`/api/jobs/${jobId}/apply`, null);
  }
}
