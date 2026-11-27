import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { PageHeader } from '../shared/page-header/page-header';
import { JoobleSearch, ProfileService, UserProfile } from './profile.service';

/**
 * Profile page: what the user is looking for, the scores under which offers leave the list,
 * and their background (used for the cover letters). Also shows the Jooble searches the LLM
 * worked out from what they are looking for.
 */
@Component({
  imports: [DatePipe, PageHeader],
  selector: 'app-profile',
  styleUrl: './profile.css',
  templateUrl: './profile.html',
})
export class Profile implements OnInit {
  private readonly profileService = inject(ProfileService);
  protected readonly i18n = inject(I18nService);

  protected readonly profile = signal<UserProfile | null>(null);
  protected readonly saving = signal(false);
  // True right after a save, until the text is changed again.
  protected readonly saved = signal(false);
  protected readonly searches = signal<JoobleSearch[]>([]);
  // null: no error. Otherwise the API's own message (e.g. the LLM failed: nothing was saved).
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.profileService.getProfile().subscribe((profile) => this.profile.set(profile));
    this.loadSearches();
  }

  protected save(
    text: string,
    background: string,
    minScoreOnsite: number,
    minScoreRemote: number,
  ): void {
    this.saving.set(true);
    this.error.set(null);
    this.profileService.saveProfile(text, background, minScoreOnsite, minScoreRemote).subscribe({
      next: (profile) => {
        this.profile.set(profile);
        this.saving.set(false);
        this.saved.set(true);
        // The searches change when what the user is looking for does.
        this.loadSearches();
      },
      // The text stays in the box, so the user can try again.
      error: (error: HttpErrorResponse) => {
        this.saving.set(false);
        const detail = error.error?.detail;
        this.error.set(typeof detail === 'string' ? detail : '');
      },
    });
  }

  private loadSearches(): void {
    this.profileService.getSearches().subscribe((searches) => this.searches.set(searches));
  }
}
