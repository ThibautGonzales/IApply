import { NgTemplateOutlet } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';
import {
  LetterExample,
  LetterExampleChange,
  LetterExamplesService,
} from './letter-examples.service';

/** What the form is open for: a new example, an existing one (its id), or nothing. */
type Editing = 'new' | number | null;

/**
 * Letter examples page: the cover letters the user already wrote. The LLM follows their style
 * when it writes a new letter. One form, used to add an example or to change one.
 */
@Component({
  imports: [NgTemplateOutlet],
  selector: 'app-letter-examples',
  styleUrl: './letter-examples.css',
  templateUrl: './letter-examples.html',
})
export class LetterExamples implements OnInit {
  private readonly examplesService = inject(LetterExamplesService);
  protected readonly i18n = inject(I18nService);

  protected readonly examples = signal<LetterExample[]>([]);
  protected readonly editing = signal<Editing>(null);
  // Deleting takes two clicks: the first one asks to confirm, as the text cannot be brought back.
  protected readonly confirmingDelete = signal<number | null>(null);
  protected readonly saving = signal(false);
  // The backend refuses an empty title or text: the form says so before sending anything.
  protected readonly missingField = signal(false);

  ngOnInit(): void {
    this.examplesService.getExamples().subscribe((examples) => this.examples.set(examples));
  }

  protected edit(editing: Editing): void {
    this.editing.set(editing);
    this.confirmingDelete.set(null);
    this.missingField.set(false);
  }

  protected save(change: LetterExampleChange): void {
    if (!change.title || !change.text) {
      this.missingField.set(true);
      return;
    }
    const editing = this.editing();
    const request =
      editing === 'new'
        ? this.examplesService.addExample(change)
        : this.examplesService.changeExample(editing as number, change);
    this.saving.set(true);
    request.subscribe({
      next: (saved) => {
        // Added at the end (the order of the list), or replaced where it was.
        this.examples.update((examples) =>
          editing === 'new'
            ? [...examples, saved]
            : examples.map((example) => (example.id === saved.id ? saved : example)),
        );
        this.saving.set(false);
        this.editing.set(null);
      },
      // The form stays open with its text, so the user can try again.
      error: () => this.saving.set(false),
    });
  }

  protected delete(example: LetterExample): void {
    if (this.confirmingDelete() !== example.id) {
      this.confirmingDelete.set(example.id);
      return;
    }
    this.examplesService.deleteExample(example.id).subscribe(() => {
      this.examples.update((examples) => examples.filter((other) => other.id !== example.id));
      this.confirmingDelete.set(null);
    });
  }
}
