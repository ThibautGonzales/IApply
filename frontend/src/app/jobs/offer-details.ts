import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CoverLetterService } from '../cover-letter/cover-letter.service';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer, JobsService } from './jobs.service';

/** Where the cover letter of the offer stands: still asked to the API, missing, or there. */
type LetterState = 'loading' | 'none' | 'ready';

/**
 * What "View offer" unfolds, on the offers page and on the tracking page: the offer details,
 * its full text (pasted by the user from the original posting), a link to that posting,
 * and its cover letter: generated here, then shown on its own page.
 */
@Component({
  selector: 'app-offer-details',
  styleUrl: './offer-details.css',
  templateUrl: './offer-details.html',
})
export class OfferDetails implements OnInit {
  private readonly jobsService = inject(JobsService);
  private readonly letterService = inject(CoverLetterService);
  private readonly router = inject(Router);
  protected readonly i18n = inject(I18nService);

  readonly job = input.required<JobOffer>();
  // Sends the updated offer so the parent can replace it in its own list.
  readonly saved = output<JobOffer>();

  protected readonly editing = signal(false);
  protected readonly saving = signal(false);
  protected readonly letter = signal<LetterState>('loading');
  protected readonly generating = signal(false);
  // null: no error. Otherwise the API's own message (no LLM set up, empty profile...).
  protected readonly letterError = signal<string | null>(null);

  ngOnInit(): void {
    // A 404 only means that no letter was generated yet.
    this.letterService.getLetter(this.job().id).subscribe({
      next: () => this.letter.set('ready'),
      error: () => this.letter.set('none'),
    });
  }

  /** Asks the LLM for the letter, then opens its page. It can take a while. */
  protected generate(): void {
    this.generating.set(true);
    this.letterError.set(null);
    this.letterService.generate(this.job().id).subscribe({
      next: () => this.openLetter(),
      error: (error: HttpErrorResponse) => {
        this.generating.set(false);
        const detail = error.error?.detail;
        this.letterError.set(typeof detail === 'string' ? detail : '');
      },
    });
  }

  protected openLetter(): void {
    this.router.navigate(['/jobs', this.job().id, 'letter']);
  }

  protected save(text: string): void {
    this.saving.set(true);
    this.jobsService.changeDescription(this.job().id, text).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.editing.set(false);
        this.saved.emit(updated);
      },
      // The text stays in the box, so the user can try again.
      error: () => this.saving.set(false),
    });
  }
}
