# Design System

## Visual Direction

A clear technical workspace emphasizing evidence and decision status. Avoid decorative effects competing with plots or warnings. Typography, spacing and contrast serve dense records and sustained reading.

## Proposed Tokens

Use semantic CSS variables for background, surface, text, muted text, border, focus, accent, warning, error and success. Choose light/dark values through contrast checks rather than assuming a palette is accessible. A 4px spacing base with 8/12/16/24/32px steps is a proposed layout convention, not a performance requirement.

Use a readable sans-serif UI font and tabular numerals for quantities. Sizes should retain legibility at browser zoom. Define chart colours consistently; status also requires text/icon meaning.

## Components

Shared controls include buttons, dialogs, status badges, asynchronous states, form fields and chart wrappers. Use Radix foundations for focus/keyboard behaviour; complete labels, errors and contrast in application code. Avoid feature-specific business rules in generic controls.

## Chart Language

Show axis units, cutoff/context, legends and a clear distinction between observations, estimates and intervals. Match labels to available metadata. Do not display a confidence band without its actual evaluated meaning.

## Review

Review tables, forms, charts and timeline views with realistic data and error states. Final tokens and screenshots become implementation artifacts after UI work; this file does not claim a completed visual design.
