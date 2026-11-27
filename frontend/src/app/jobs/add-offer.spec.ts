import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AddOffer } from './add-offer';
import { ExtractedOffer, JobOffer } from './jobs.service';

const PASTED_TEXT = 'Développeur Python - Acme - Lyon - CDI';
const URL = 'https://www.linkedin.com/jobs/view/123';

const fields: ExtractedOffer = {
  title: 'Développeur Python',
  company: 'Acme',
  location: 'Lyon',
  contract_type: 'CDI',
  salary: null,
  remote: false,
};

function type(element: HTMLInputElement | HTMLTextAreaElement | null, value: string): void {
  element!.value = value;
  element!.dispatchEvent(new Event('input'));
}

describe('AddOffer', () => {
  let httpTesting: HttpTestingController;
  let fixture: ComponentFixture<AddOffer>;
  let compiled: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddOffer],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(AddOffer);
    compiled = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  /** Pastes the text and the link, and lets the LLM read the offer. */
  async function readTheOffer(): Promise<void> {
    type(compiled.querySelector('.text'), PASTED_TEXT);
    type(compiled.querySelector('.url'), URL);
    await fixture.whenStable();
    compiled.querySelector<HTMLButtonElement>('.read')?.click();
    const request = httpTesting.expectOne({ method: 'POST', url: '/api/jobs/manual/extract' });
    expect(request.request.body).toEqual({ text: PASTED_TEXT });
    request.flush(fields);
    await fixture.whenStable();
  }

  it('shows the fields read by the LLM, ready to be checked', async () => {
    await readTheOffer();

    expect(compiled.querySelector<HTMLInputElement>('.title')?.value).toBe('Développeur Python');
    expect(compiled.querySelector<HTMLInputElement>('.company')?.value).toBe('Acme');
    expect(compiled.querySelector<HTMLInputElement>('.salary')?.value).toBe('');
  });

  it('saves the checked fields with the link and the pasted text', async () => {
    const added: JobOffer[] = [];
    fixture.componentInstance.added.subscribe((offer) => added.push(offer));
    await readTheOffer();

    type(compiled.querySelector('.company'), 'Acme Lyon');
    compiled.querySelector<HTMLInputElement>('.remote')!.checked = true;
    compiled.querySelector<HTMLButtonElement>('.save')?.click();
    const request = httpTesting.expectOne({ method: 'POST', url: '/api/jobs/manual' });
    expect(request.request.body).toEqual({
      ...fields,
      company: 'Acme Lyon',
      remote: true,
      url: URL,
      description: PASTED_TEXT,
    });
    request.flush({ id: 7, source: 'manual', title: 'Développeur Python' });
    await fixture.whenStable();

    expect(added.map((offer) => offer.id)).toEqual([7]);
  });

  it('asks the offers page to close the form on cancel', async () => {
    let closed = false;
    fixture.componentInstance.closed.subscribe(() => (closed = true));

    compiled.querySelector<HTMLButtonElement>('.cancel')?.click();

    expect(closed).toBe(true);
  });

  it('does not save an offer without a link', async () => {
    await readTheOffer();
    type(compiled.querySelector('.url'), '  ');

    compiled.querySelector<HTMLButtonElement>('.save')?.click();
    await fixture.whenStable();

    httpTesting.expectNone('/api/jobs/manual');
    expect(compiled.querySelector('.error')?.textContent).toContain(
      'A title and a link are needed.',
    );
  });

  it("shows the API's message when the offer cannot be read", async () => {
    type(compiled.querySelector('.text'), PASTED_TEXT);
    await fixture.whenStable();

    compiled.querySelector<HTMLButtonElement>('.read')?.click();
    httpTesting
      .expectOne('/api/jobs/manual/extract')
      .flush(
        { detail: 'Could not read the offer: no API key' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(compiled.querySelector('.error')?.textContent).toContain(
      'Could not read the offer: no API key',
    );
  });
});
