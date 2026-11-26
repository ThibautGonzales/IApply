import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Profile } from './profile';
import { UserProfile } from './profile.service';

const profile: UserProfile = {
  looking_for: 'Python backend developer, Clermont-Ferrand or remote',
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
  });

  it('saves the text and confirms it', async () => {
    const { fixture, compiled } = await render({ ...profile, looking_for: '' });

    compiled.querySelector('textarea')!.value = 'AI developer, remote';
    compiled.querySelector('button')!.click();
    const request = httpTesting.expectOne('/api/profile');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({ looking_for: 'AI developer, remote' });
    request.flush({ ...profile, looking_for: 'AI developer, remote' });
    fixture.detectChanges();
    await fixture.whenStable();

    expect(compiled.querySelector('.saved')?.textContent).toContain('Saved');
  });
});
