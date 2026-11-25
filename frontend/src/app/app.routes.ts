import { Routes } from '@angular/router';
import { Applications } from './applications/applications';
import { Jobs } from './jobs/jobs';

export const routes: Routes = [
  { path: '', component: Jobs },
  { path: 'applications', component: Applications },
  // Any unknown address goes back to the offers.
  { path: '**', redirectTo: '' },
];
