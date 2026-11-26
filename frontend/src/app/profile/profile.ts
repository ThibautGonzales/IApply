import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import { ProfileService, UserProfile } from './profile.service';

/** Profile page: what the user is looking for, and the score under which offers leave the list. */
@Component({
  imports: [DatePipe],
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

  ngOnInit(): void {
    this.profileService.getProfile().subscribe((profile) => this.profile.set(profile));
  }

  protected save(text: string, minScore: number): void {
    this.saving.set(true);
    this.profileService.saveProfile(text, minScore).subscribe({
      next: (profile) => {
        this.profile.set(profile);
        this.saving.set(false);
        this.saved.set(true);
      },
      // The text stays in the box, so the user can try again.
      error: () => this.saving.set(false),
    });
  }
}
