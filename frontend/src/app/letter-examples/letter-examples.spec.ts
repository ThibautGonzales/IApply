import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { LetterExamples } from './letter-examples';
import { LetterExample } from './letter-examples.service';

const michelin: LetterExample = {
  id: 1,
  title: 'Data engineer at Michelin',
  text: 'Dear Sir or Madam, ...',
  created_at: '2026-11-27T13:00:00Z',
};

describe('LetterExamples', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [LetterExamples],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(examples: LetterExample[]) {
    const fixture = TestBed.createComponent(LetterExamples);
    fixture.detectChanges();
    httpTesting.expectOne('/api/letter-examples').flush(examples);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  function click(compiled: HTMLElement, selector: string): void {
    compiled.querySelector<HTMLButtonElement>(selector)!.click();
  }

  function fill(compiled: HTMLElement, title: string, text: string): void {
    compiled.querySelector<HTMLInputElement>('input.title')!.value = title;
    compiled.querySelector<HTMLTextAreaElement>('textarea.text')!.value = text;
  }

  it('lists the examples by their title', async () => {
    const { compiled } = await render([michelin]);

    expect(compiled.querySelector('h3')?.textContent).toContain('Data engineer at Michelin');
  });

  it('adds an example at the end of the list', async () => {
    const { fixture, compiled } = await render([michelin]);

    click(compiled, '.add');
    await fixture.whenStable();
    fill(compiled, 'Python developer at OVH', 'Hello, ...');
    click(compiled, '.save');
    const request = httpTesting.expectOne({ method: 'POST', url: '/api/letter-examples' });
    expect(request.request.body).toEqual({ title: 'Python developer at OVH', text: 'Hello, ...' });
    request.flush({ ...michelin, id: 2, title: 'Python developer at OVH', text: 'Hello, ...' });
    await fixture.whenStable();

    const titles = [...compiled.querySelectorAll('h3')].map((title) => title.textContent?.trim());
    expect(titles).toEqual(['Data engineer at Michelin', 'Python developer at OVH']);
  });

  it('does not send an example without text', async () => {
    const { fixture, compiled } = await render([]);

    click(compiled, '.add');
    await fixture.whenStable();
    fill(compiled, 'A title', '  ');
    click(compiled, '.save');
    await fixture.whenStable();

    httpTesting.expectNone('/api/letter-examples');
    expect(compiled.querySelector('.error')?.textContent).toContain('required');
  });

  it('changes an example with the text it already has in the form', async () => {
    const { fixture, compiled } = await render([michelin]);

    click(compiled, '.edit');
    await fixture.whenStable();
    expect(compiled.querySelector<HTMLTextAreaElement>('textarea.text')?.value).toBe(michelin.text);
    fill(compiled, 'New title', 'New text');
    click(compiled, '.save');
    httpTesting
      .expectOne({ method: 'PUT', url: '/api/letter-examples/1' })
      .flush({ ...michelin, title: 'New title', text: 'New text' });
    await fixture.whenStable();

    expect(compiled.querySelector('h3')?.textContent).toContain('New title');
  });

  it('deletes an example only on the second click', async () => {
    const { fixture, compiled } = await render([michelin]);

    click(compiled, '.delete');
    await fixture.whenStable();
    httpTesting.expectNone('/api/letter-examples/1');
    click(compiled, '.delete');
    httpTesting.expectOne({ method: 'DELETE', url: '/api/letter-examples/1' }).flush(null);
    await fixture.whenStable();

    expect(compiled.textContent).toContain('No letter yet.');
  });
});
