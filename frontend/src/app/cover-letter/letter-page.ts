import { DatePipe, Location } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { I18nService } from '../core/i18n/i18n.service';
import { JobOffer, JobsService } from '../jobs/jobs.service';
import { PageHeader } from '../shared/page-header/page-header';
import { CoverLetter, CoverLetterService, Replacement } from './cover-letter.service';

/**
 * Cover letter page (`/jobs/:id/letter`): the letter of one offer, to change by hand or by asking
 * the LLM, then to copy. Opened from "View offer", once the letter is generated.
 */
@Component({
  imports: [DatePipe, PageHeader],
  selector: 'app-letter-page',
  styleUrl: './letter-page.css',
  templateUrl: './letter-page.html',
})
export class LetterPage implements OnInit {
  private readonly jobsService = inject(JobsService);
  private readonly letterService = inject(CoverLetterService);
  private readonly location = inject(Location);
  protected readonly i18n = inject(I18nService);

  // The `:id` of the address, given by the router (withComponentInputBinding in app.config.ts).
  readonly id = input.required<string>();

  protected readonly job = signal<JobOffer | null>(null);
  protected readonly letter = signal<CoverLetter | null>(null);
  // The text in the box, changed by hand or by the LLM. Saved when it equals the letter's text.
  protected readonly text = signal('');
  protected readonly unsaved = computed(() => this.text() !== (this.letter()?.text ?? ''));
  protected readonly instructions = signal('');
  // One call at a time: every button waits for the API.
  protected readonly busy = signal(false);
  // Regenerating replaces the whole letter: the first click asks to confirm.
  protected readonly confirmingRegenerate = signal(false);
  protected readonly copied = signal(false);
  // The replacements the LLM asked for but that could not be made, after the last change.
  protected readonly failed = signal<Replacement[]>([]);
  // null: no error. Otherwise the API's own message.
  protected readonly error = signal<string | null>(null);

  private get jobId(): number {
    return Number(this.id());
  }

  ngOnInit(): void {
    this.jobsService.getJob(this.jobId).subscribe((job) => this.job.set(job));
    this.letterService.getLetter(this.jobId).subscribe((letter) => this.show(letter));
  }

  protected save(): void {
    this.call(this.letterService.save(this.jobId, this.text()), (letter) => this.show(letter));
  }

  protected revise(): void {
    const request = this.letterService.revise(this.jobId, this.text(), this.instructions().trim());
    this.call(request, (revised) => {
      this.show(revised.letter);
      this.failed.set(revised.failed);
      this.instructions.set('');
    });
  }

  protected regenerate(): void {
    if (!this.confirmingRegenerate()) {
      this.confirmingRegenerate.set(true);
      return;
    }
    this.confirmingRegenerate.set(false);
    this.call(this.letterService.generate(this.jobId), (letter) => this.show(letter));
  }

  protected copy(): void {
    navigator.clipboard.writeText(this.text()).then(() => this.copied.set(true));
  }

  protected back(): void {
    this.location.back();
  }

  protected edit(text: string): void {
    this.text.set(text);
    this.copied.set(false);
  }

  /** The letter as saved by the API: its text goes back in the box. */
  private show(letter: CoverLetter): void {
    this.letter.set(letter);
    this.text.set(letter.text);
    this.copied.set(false);
  }

  /** Shared by the buttons: one call at a time, and the API's message if it fails. */
  private call<T>(request: Observable<T>, done: (answer: T) => void): void {
    this.busy.set(true);
    this.error.set(null);
    this.failed.set([]);
    request.subscribe({
      next: (answer) => {
        this.busy.set(false);
        done(answer);
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        const detail = error.error?.detail;
        this.error.set(typeof detail === 'string' ? detail : '');
      },
    });
  }
}
