import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Profile } from './profile';
import { UserProfile } from './profile.service';

const profile: UserProfile = {
  looking_for: 'Python backend developer, Clermont-Ferrand or remote',
  min_score_onsite: 50,
  min_score_remote: 70,
  updated_at: '2026-11-26T13:00:00Z',
};

describe('Profile', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Profile],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(saved: UserProfile) {
    const fixture = TestBed.createComponent(Profile);
    fixture.detectChanges();
    httpTesting.expectOne('/api/profile').flush(saved);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  it('shows the saved profile in the text box', async () => {
    const { compiled } = await render(profile);

    expect(compiled.querySelector('textarea')?.value).toBe(profile.looking_for);
    expect(compiled.querySelector<HTMLInputElement>('.onsite')?.value).toBe('50');
    expect(compiled.querySelector<HTMLInputElement>('.remote')?.value).toBe('70');
  });

  it('saves the text and confirms it', async () => {
    const { fixture, compiled } = await render({ ...profile, looking_for: '' });

    compiled.querySelector('textarea')!.value = 'AI developer, remote';
    compiled.querySelector<HTMLInputElement>('.onsite')!.value = '65';
    compiled.querySelector<HTMLInputElement>('.remote')!.value = '80';
    compiled.querySelector('button')!.click();
    const request = httpTesting.expectOne('/api/profile');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({
      looking_for: 'AI developer, remote',
      min_score_onsite: 65,
      min_score_remote: 80,
    });
    request.flush({
      ...profile,
      looking_for: 'AI developer, remote',
      min_score_onsite: 65,
      min_score_remote: 80,
    });
    fixture.detectChanges();
    await fixture.whenStable();

    expect(compiled.querySelector('.saved')?.textContent).toContain('Saved');
  });
});
