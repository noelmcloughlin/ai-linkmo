<script lang="ts">
    let {
        position = "left",   // left or right
        color = "green",     // Button color
        icon = "X",         // Button icon
        ariaLabel = "Toggle menu",  // Accessibility label
        onClick = (event: MouseEvent & { currentTarget: HTMLButtonElement }) => {},  // Click handler
        style = "",          // Additional styles
        px = "3",             // Horizontal padding
        py = "2",             // Vertical padding
        textSize = "lg",     // Text size
    } = $props();
</script>

<button
    class={`fixed ${position}-2 z-50 bg-${color}-600 text-white rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-${color}-400 transition-all duration-150 px-${px} py-${py} text-${textSize}`}
    style={style}
    type="button"
    aria-label={ariaLabel}
    onclick={(event) => onClick(event as MouseEvent & { currentTarget: HTMLButtonElement })}
>
    {icon}
</button>