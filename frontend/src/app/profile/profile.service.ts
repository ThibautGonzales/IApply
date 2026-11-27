import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** What the user is looking for and their background, as returned by the backend `UserProfile`. */
export interface UserProfile {
  looking_for: string;
  /** Skills, career and work experience: only used for the cover letters. */
  background: string;
  /** Offers scored under their threshold (0-100) leave the list: on-site or hybrid offers... */
  min_score_onsite: number;
  /** ...and full remote offers. */
  min_score_remote: number;
  updated_at: string;
}

/** One Jooble query of the collection, worked out by the LLM from `looking_for` (backend `JoobleSearch`). */
export interface JoobleSearch {
  id: number;
  keywords: string;
  /** Full remote offers, anywhere: no location nor radius then. */
  remote: boolean;
  location: string | null;
  radius_km: number | null;
}

/** Talks to the backend `/profile` routes. */
@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>('/api/profile');
  }

  getSearches(): Observable<JoobleSearch[]> {
    return this.http.get<JoobleSearch[]>('/api/profile/searches');
  }

  saveProfile(
    lookingFor: string,
    background: string,
    minScoreOnsite: number,
    minScoreRemote: number,
  ): Observable<UserProfile> {
    return this.http.put<UserProfile>('/api/profile', {
      looking_for: lookingFor,
      background,
      min_score_onsite: minScoreOnsite,
      min_score_remote: minScoreRemote,
    });
  }
}
