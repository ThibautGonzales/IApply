import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** The cover letter of an offer, as returned by the backend `CoverLetter`. */
export interface CoverLetter {
  id: number;
  job_offer_id: number;
  text: string;
  updated_at: string;
}

/** A change asked by the LLM: replace `old`, copied from the letter, with `new`. */
export interface Replacement {
  old: string;
  new: string;
}

/** What a change by the LLM returns: the saved letter, and the replacements that could not be made. */
export interface RevisedLetter {
  letter: CoverLetter;
  failed: Replacement[];
}

/** Talks to the backend `/jobs/{id}/cover-letter` routes. */
@Injectable({ providedIn: 'root' })
export class CoverLetterService {
  private readonly http = inject(HttpClient);

  /** Fails with a 404 while no letter was generated for the offer. */
  getLetter(jobId: number): Observable<CoverLetter> {
    return this.http.get<CoverLetter>(`/api/jobs/${jobId}/cover-letter`);
  }

  /** Asks the LLM for a new letter, which replaces the one there was. */
  generate(jobId: number): Observable<CoverLetter> {
    return this.http.post<CoverLetter>(`/api/jobs/${jobId}/cover-letter`, {});
  }

  /** Saves the letter changed by hand. */
  save(jobId: number, text: string): Observable<CoverLetter> {
    return this.http.put<CoverLetter>(`/api/jobs/${jobId}/cover-letter`, { text });
  }

  /** Asks the LLM to change `text` (the letter shown on the page) following the instructions. */
  revise(jobId: number, text: string, instructions: string): Observable<RevisedLetter> {
    return this.http.post<RevisedLetter>(`/api/jobs/${jobId}/cover-letter/revise`, {
      text,
      instructions,
    });
  }
}
