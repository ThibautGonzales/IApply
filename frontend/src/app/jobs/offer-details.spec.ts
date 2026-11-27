import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { OfferDetails } from './offer-details';
import { JobOffer } from './jobs.service';

const offer: JobOffer = {
  id: 1,
  source: 'manual',
  external_id: 'abc',
  title: 'Python developer',
  company: 'ACME',
  location: 'Lyon',
  salary: null,
  contract_type: 'CDI',
  description: 'We are looking for a Python developer.',
  url: 'https://example.com/1',
  remote: false,
  hidden: false,
  restored: false,
  score: null,
  published_at: '2026-11-27T09:00:00Z',
  collected_at: '2026-11-27T09:00:00Z',
};
const letter = {
  id: 3,
  job_offer_id: 1,
  text: 'Dear Sir or Madam',
  updated_at: '2026-11-27T10:00:00Z',
};
const notFound = { status: 404, statusText: 'Not Found' };

describe('OfferDetails', () => {
  let httpTesting: HttpTestingController;
  let navigate: ReturnType<typeof vi.spyOn>;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [OfferDetails],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
    navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
  });

  async function render(job: JobOffer, existingLetter: object | null) {
    const fixture = TestBed.createComponent(OfferDetails);
    fixture.componentRef.setInput('job', job);
    fixture.detectChanges();
    const request = httpTesting.expectOne('/api/jobs/1/cover-letter');
    if (existingLetter) {
      request.flush(existingLetter);
    } else {
      request.flush(null, notFound);
    }
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  it('cannot generate a letter before the offer text is pasted', async () => {
    const { compiled } = await render({ ...offer, description: null }, null);

    expect(compiled.querySelector<HTMLButtonElement>('.generate')?.disabled).toBe(true);
    expect(compiled.querySelector('.letter small')?.textContent).toContain('Paste the offer text');
  });

  it('generates the letter, then opens its page', async () => {
    const { compiled } = await render(offer, null);

    compiled.querySelector<HTMLButtonElement>('.generate')!.click();
    httpTesting.expectOne({ method: 'POST', url: '/api/jobs/1/cover-letter' }).flush(letter);

    expect(navigate).toHaveBeenCalledWith(['/jobs', 1, 'letter']);
  });

  it('shows the error of the API when the letter cannot be written', async () => {
    const { fixture, compiled } = await render(offer, null);

    compiled.querySelector<HTMLButtonElement>('.generate')!.click();
    httpTesting
      .expectOne({ method: 'POST', url: '/api/jobs/1/cover-letter' })
      .flush({ detail: 'Choose a provider' }, { status: 400, statusText: 'Bad Request' });
    await fixture.whenStable();

    expect(compiled.querySelector('.letter .error')?.textContent).toContain('Choose a provider');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('opens the letter when there is one already', async () => {
    const { compiled } = await render(offer, letter);

    expect(compiled.querySelector('.generate')).toBeNull();
    compiled.querySelector<HTMLButtonElement>('.open-letter')!.click();

    expect(navigate).toHaveBeenCalledWith(['/jobs', 1, 'letter']);
  });
});
