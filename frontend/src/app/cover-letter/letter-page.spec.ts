import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { LetterPage } from './letter-page';
import { CoverLetter } from './cover-letter.service';

const letter: CoverLetter = {
  id: 3,
  job_offer_id: 1,
  text: 'Dear Sir or Madam, I like Python.',
  updated_at: '2026-11-27T10:00:00Z',
};
const job = { id: 1, title: 'Python developer', company: 'ACME', url: 'https://example.com/1' };

describe('LetterPage', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [LetterPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render() {
    const fixture = TestBed.createComponent(LetterPage);
    fixture.componentRef.setInput('id', '1');
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs/1').flush(job);
    httpTesting.expectOne({ method: 'GET', url: '/api/jobs/1/cover-letter' }).flush(letter);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  function type(compiled: HTMLElement, selector: string, value: string): void {
    const box = compiled.querySelector<HTMLTextAreaElement>(selector)!;
    box.value = value;
    box.dispatchEvent(new Event('input'));
  }

  function button(compiled: HTMLElement, selector: string): HTMLButtonElement {
    return compiled.querySelector<HTMLButtonElement>(selector)!;
  }

  it('shows the offer and its letter', async () => {
    const { compiled } = await render();

    expect(compiled.querySelector('.job a')?.textContent).toContain('Python developer');
    expect(compiled.querySelector<HTMLTextAreaElement>('textarea.text')?.value).toBe(letter.text);
    expect(button(compiled, '.save').disabled).toBe(true); // nothing to save yet
  });

  it('saves a change made by hand', async () => {
    const { fixture, compiled } = await render();

    type(compiled, 'textarea.text', 'My own letter');
    await fixture.whenStable();
    expect(compiled.querySelector('.status')?.textContent).toContain('Changes not saved');
    button(compiled, '.save').click();
    const request = httpTesting.expectOne({ method: 'PUT', url: '/api/jobs/1/cover-letter' });
    expect(request.request.body).toEqual({ text: 'My own letter' });
    request.flush({ ...letter, text: 'My own letter' });
    await fixture.whenStable();

    expect(compiled.querySelector('.status')?.textContent).toContain('Saved on');
  });

  it('sends the text in the box with the instructions, and lists what could not be changed', async () => {
    const { fixture, compiled } = await render();

    type(compiled, 'textarea.text', 'Hello, I like Python.'); // changed by hand, not saved
    type(compiled, 'textarea.instructions', 'Talk about Go');
    await fixture.whenStable();
    button(compiled, '.revise').click();
    const request = httpTesting.expectOne({
      method: 'POST',
      url: '/api/jobs/1/cover-letter/revise',
    });
    expect(request.request.body).toEqual({
      text: 'Hello, I like Python.',
      instructions: 'Talk about Go',
    });
    request.flush({
      letter: { ...letter, text: 'Hello, I like Go.' },
      failed: [{ old: 'Kotlin', new: 'Rust' }],
    });
    await fixture.whenStable();

    expect(compiled.querySelector<HTMLTextAreaElement>('textarea.text')?.value).toBe(
      'Hello, I like Go.',
    );
    expect(compiled.querySelector<HTMLTextAreaElement>('textarea.instructions')?.value).toBe('');
    expect(compiled.querySelector('.failed li')?.textContent).toContain('Kotlin');
  });

  it('writes a new letter only on the second click', async () => {
    const { fixture, compiled } = await render();

    button(compiled, '.regenerate').click();
    await fixture.whenStable();
    httpTesting.expectNone({ method: 'POST', url: '/api/jobs/1/cover-letter' });
    expect(button(compiled, '.regenerate').textContent).toContain('Click again');
    button(compiled, '.regenerate').click();
    httpTesting
      .expectOne({ method: 'POST', url: '/api/jobs/1/cover-letter' })
      .flush({ ...letter, text: 'A brand new letter' });
    await fixture.whenStable();

    expect(compiled.querySelector<HTMLTextAreaElement>('textarea.text')?.value).toBe(
      'A brand new letter',
    );
  });
});
