// lib/frontend/src/lib/utils/ui.ts
import { uiState } from "$states/index";

export function setElementWidths(elements: HTMLElement[], width: number) {
  elements.forEach((el: HTMLElement) => {
    if (el) el.style.width = `${width}px`;
  });
}

export function handleResponsiveUI() {
    // static widths from header, main, and footer
    const elements = [
      document.querySelector("header"),
      document.querySelector("main"),
      document.querySelector("footer"),
    ];
    setElementWidths(
      elements.filter((el): el is HTMLElement => el !== null),
      uiState.windowWidth,
    );
  }
