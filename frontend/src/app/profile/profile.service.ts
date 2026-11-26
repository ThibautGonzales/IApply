import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** What the user is looking for, as returned by the backend `UserProfile`. */
export interface UserProfile {
  looking_for: string;
  /** Offers scored under this threshold (0-100) leave the list. */
  min_score: number;
  updated_at: string;
}

/** Talks to the backend `/profile` routes. */
@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>('/api/profile');
  }

  saveProfile(lookingFor: string, minScore: number): Observable<UserProfile> {
    return this.http.put<UserProfile>('/api/profile', {
      looking_for: lookingFor,
      min_score: minScore,
    });
  }
}
