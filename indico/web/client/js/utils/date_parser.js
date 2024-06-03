// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

const TOKEN_START = Symbol('start');
const TOKEN_ANY = Symbol('any');
const TOKEN_MONTH = Symbol('month');
const TOKEN_YEAR = Symbol('year');
const TOKEN_DATE = Symbol('date');
const CHAR_TO_TOKEN_TYPE = {
  y: TOKEN_YEAR,
  Y: TOKEN_YEAR,
  m: TOKEN_MONTH,
  M: TOKEN_MONTH,
  d: TOKEN_DATE,
  D: TOKEN_DATE,
};

export function createDateParser(formatString) {
  const tokens = [];
  const tokenTypesFound = new Set();
  let lastCharType = TOKEN_START;
  const buffer = [];

  formatString = formatString.toLowerCase();

  // Tokenize
  for (let i = 0; i < formatString.length; i++) {
    const char = formatString[i];
    const type = CHAR_TO_TOKEN_TYPE[char] || TOKEN_ANY;

    if (type !== lastCharType && buffer.length) {
      tokenTypesFound.add(lastCharType);
      tokens.push({
        type: lastCharType,
        text: buffer.join(''),
      });
      buffer.length = 0;
    }

    buffer.push(char);
    lastCharType = type;
  }

  if (buffer.length) {
    tokenTypesFound.add(lastCharType);
    tokens.push({
      type: lastCharType,
      text: buffer.join(''),
    });
  }

  // Sanity check
  if (
    !tokenTypesFound.has(TOKEN_YEAR) ||
    !tokenTypesFound.has(TOKEN_MONTH) ||
    !tokenTypesFound.has(TOKEN_DATE)
  ) {
    throw Error('Invalid date format: date format must include year, month, and date');
  }

  // Convert tokens to regex
  let regexSource = '^';
  for (const token of tokens) {
    switch (token.type) {
      case TOKEN_YEAR:
        regexSource += '(?<year>\\d{4})';
        break;
      case TOKEN_MONTH:
        regexSource += '(?<month>1[012]|0?[1-9])';
        break;
      case TOKEN_DATE:
        regexSource += '(?<date>3[01]|[12][0-9]|0?[1-9])';
        break;
      default:
        regexSource += `\\D{${token.text.length}}`;
    }
  }
  regexSource += '$';
  const regex = new RegExp(regexSource);

  // Crate the parser function
  return function(text) {
    const match = regex.exec(text);
    if (match) {
      const year = Number(match.groups.year);
      const month = Number(match.groups.month) - 1;
      const date = Number(match.groups.date);
      const output = new Date(year, month, date);

      // JavaScript's Date constructor is too lenient when it comes to invalid
      // combinations of month and date. For example, 2024-02-31 will be treated
      // as 2021-03-02 (two days carrying over to March). We therefore reject
      // inputs where the month does not match the input.
      if (output.getMonth() !== month) {
        return;
      }

      return output;
    }
  };
}

export function fromISOLocalDate(dateString) {
  if (!dateString) {
    return;
  }
  const [year, month, date] = dateString.split('-');
  return new Date(year, month - 1, date);
}
