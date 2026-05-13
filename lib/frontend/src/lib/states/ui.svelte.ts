// Some ui states
export const responsiveConfig = [
    { maxWidth: 640, const: "max-w-xs" },
    { maxWidth: 768, const: "max-w-md" },
    { maxWidth: 1024, const: "max-w-lg" },
    { maxWidth: 1280, const: "max-w-xl" },
    { maxWidth: 1536, const: "max-w-2xl" },
    { maxWidth: 1800, const: "max-w-4xl" },
    { maxWidth: Infinity, const: "max-w-screen-2xl" },
];

// Extended responsive config from when right aside is hidden
export const responsiveConfigExpanded = [
    { maxWidth: 640, const: "max-w-md" },
    { maxWidth: 768, const: "max-w-lg" },
    { maxWidth: 1024, const: "max-w-xl" },
    { maxWidth: 1280, const: "max-w-2xl" },
    { maxWidth: 1536, const: "max-w-4xl" },
    { maxWidth: 1800, const: "max-w-6xl" },
    { maxWidth: Infinity, const: "max-w-screen-2xl" },
];

class UiState {
    windowWidth = $state(window.innerWidth);
    rightAsideOpen = $state(true);

    get cardWidthClass(): string {
        const config = this.rightAsideOpen ? responsiveConfig : responsiveConfigExpanded;
        for (const { maxWidth, const: widthClass } of config) {
            if (this.windowWidth < maxWidth) {
                return widthClass;
            }
        }
        // Fallback instanceof catch no match
        return "max-w-screen-2xl";
    }

    getCardWidthClass(width: number = this.windowWidth): string {
        for (const { maxWidth, const: widthClass } of responsiveConfig) {
            if (width < maxWidth) {
                return widthClass;
            }
        }
        // Fallback instanceof catch no match
        return "max-w-screen-2xl";
    }
}
export const uiState = new UiState();