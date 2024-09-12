import {Moment} from 'moment';

export function formatTimeRange(locale: string, startDate: Moment, endDate: Moment): string {
  const options: Intl.DateTimeFormatOptions = {hour: 'numeric', minute: 'numeric'};
  const dateTimeFormat = new Intl.DateTimeFormat(locale, options);
  return dateTimeFormat.formatRange(startDate.toDate(), endDate.toDate());
}
