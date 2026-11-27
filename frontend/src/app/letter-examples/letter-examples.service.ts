import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** A cover letter the user already wrote, as returned by the backend `CoverLetterExample`. */
export interface LetterExample {
  id: number;
  title: string;
  text: string;
  created_at: string;
}

/** What the form sends: the same for adding and for changing an example. */
export interface LetterExampleChange {
  title: string;
  text: string;
}

/** Talks to the backend `/letter-examples` routes. */
@Injectable({ providedIn: 'root' })
export class LetterExamplesService {
  private readonly http = inject(HttpClient);

  getExamples(): Observable<LetterExample[]> {
    return this.http.get<LetterExample[]>('/api/letter-examples');
  }

  addExample(change: LetterExampleChange): Observable<LetterExample> {
    return this.http.post<LetterExample>('/api/letter-examples', change);
  }

  changeExample(id: number, change: LetterExampleChange): Observable<LetterExample> {
    return this.http.put<LetterExample>(`/api/letter-examples/${id}`, change);
  }

  deleteExample(id: number): Observable<void> {
    return this.http.delete<void>(`/api/letter-examples/${id}`);
  }
}
