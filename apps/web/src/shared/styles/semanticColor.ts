/** Canvas and SVG charts read the same semantic tokens as the DOM. */
export function semanticColor(name:string):string { return getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim(); }
