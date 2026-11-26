import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Llm } from './llm';
import { LlmSettings } from './llm.service';

const providers = [
  { id: 'openai', label: 'OpenAI', default_model: 'gpt-5-mini' },
  { id: 'anthropic', label: 'Anthropic (Claude)', default_model: 'claude-haiku-5-5' },
];
const empty: LlmSettings = { provider: null, model: null, api_key_hint: null, providers };
const configured: LlmSettings = {
  provider: 'anthropic',
  model: 'claude-haiku-5-5',
  api_key_hint: '…1234',
  providers,
};

describe('Llm', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Llm],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(saved: LlmSettings) {
    const fixture = TestBed.createComponent(Llm);
    fixture.detectChanges();
    httpTesting.expectOne('/api/llm').flush(saved);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  function type(input: HTMLInputElement, value: string) {
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  it('shows the saved provider, the default model as a hint and the end of the key', async () => {
    const { compiled } = await render(configured);

    expect(compiled.querySelector('select')?.value).toBe('anthropic');
    const model = compiled.querySelector<HTMLInputElement>('input[type=text]')!;
    expect(model.value).toBe('');
    expect(model.placeholder).toBe('claude-haiku-5-5');
    expect(compiled.textContent).toContain('…1234');
  });

  it('sends the typed key and model, and never shows the key again', async () => {
    const { fixture, compiled } = await render(empty);

    type(compiled.querySelector<HTMLInputElement>('input[type=password]')!, 'sk-ant-secret-1234');
    type(compiled.querySelector<HTMLInputElement>('input[type=text]')!, 'claude-opus-5-5');
    await fixture.whenStable();
    compiled.querySelector<HTMLButtonElement>('button.save')!.click();
    const request = httpTesting.expectOne('/api/llm');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({
      model: 'claude-opus-5-5',
      api_key: 'sk-ant-secret-1234',
    });
    request.flush({ ...configured, model: 'claude-opus-5-5' });
    fixture.detectChanges();
    await fixture.whenStable();

    expect(compiled.querySelector<HTMLInputElement>('input[type=password]')!.value).toBe('');
    expect(compiled.querySelector('.feedback')?.textContent).toContain('Saved');
  });

  it("shows the provider's error when the test fails", async () => {
    const { fixture, compiled } = await render(configured);

    compiled.querySelector<HTMLButtonElement>('button.test')!.click();
    httpTesting
      .expectOne('/api/llm/test')
      .flush(
        { detail: 'Could not reach the model: invalid x-api-key' },
        { status: 400, statusText: 'Bad Request' },
      );
    fixture.detectChanges();
    await fixture.whenStable();

    const feedback = compiled.querySelector('.feedback')!;
    expect(feedback.classList).toContain('error');
    expect(feedback.textContent).toContain('invalid x-api-key');
  });
});
