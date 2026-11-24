import { DatePipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { JobOffer } from './jobs.service';

/** Table of job offers, each title linking to the original posting. */
@Component({
  imports: [DatePipe],
  selector: 'app-job-table',
  styleUrl: './job-table.css',
  templateUrl: './job-table.html',
})
export class JobTable {
  readonly jobs = input.required<JobOffer[]>();
}
