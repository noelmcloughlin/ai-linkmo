<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { tv } from 'tailwind-variants';

  const dispatch = createEventDispatcher();

  let {
    id = "mybutton",
    type = "button" as "button" | "submit" | "reset",  // Explicitly cast to the correct type
    variant = "default" as "default" | "curate" | "outline" | "info" | "success" | "login" | "add" | "edit",
    size = "md" as "xs" | "sm" | "md" | "lg" | "xlg" | "xxlg",
    disabled = false,
    fullWidth = false,  // Control width instead of hardcoding in variants
    className = "",
    style = "",
    ariaLabel = "",  // For icon-only buttons
    ariaHaspopup = false,
    ariaExpanded = false,
    tabIndex = 0 as 0 | -1,  // Allow 0 (normal) or -1 (remove from tab order)
    onClick = (event: MouseEvent & { currentTarget: HTMLButtonElement }): void => { void event; },  // Click handler
    children,
  }: {
    id?: string;
    type?: "button" | "submit" | "reset";
    variant?: "default" | "curate" | "outline" | "info" | "success" | "login" | "add" | "edit";
    size?: "xs" | "sm" | "md" | "lg" | "xlg" | "xxlg";
    disabled?: boolean;
    fullWidth?: boolean;
    className?: string;
    style?: string;
    ariaLabel?: string;
    ariaHaspopup?: boolean;
    ariaExpanded?: boolean;
    tabIndex?: 0 | -1;
    onClick?: (event: MouseEvent & { currentTarget: HTMLButtonElement }) => void;
    children: import('svelte').Snippet;  // Allow any content inside the button
  } = $props();

  // Improved Tailwaind Variants for Button
  export const buttonVariants = tv({
    base: [
    "font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1",
    "inline-flex items-center justify-center gap-2 text-center",
    "rounded-full",  // Consistent border radius
    ],
    variants: {
        variant: {
            default: 'bg-white hover:bg-slate-100 text-black focus:ring-slate-300',
            outline: 'bg-transparent border-2 border-slate-400 text-slate-700 hover:bg-slate-100 focus:ring-slate-400',
            info: 'bg-blue-500 hover:bg-blue-600 text-white focus:ring-blue-400 active:bg-blue-700',
            success: 'bg-green-500 hover:bg-green-600 text-white focus:ring-green-400 active:bg-green-700',
            curate: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-400 active:bg-red-800',
            login: 'bg-white text-blue-700 font-semibold border border-blue-200 hover:bg-blue-50 shadow focus:ring-blue-300 min-w-[48px]',
            edit: 'bg-yellow-100 border border-yellow-400 text-yellow-800 hover:bg-yellow-200 hover:text-yellow-900 focus:ring-yellow-400',
            add: 'bg-green-100 border border-green-400 text-green-800 hover:bg-green-200 hover:text-green-900 focus:ring-green-400',
        },
        size: {
            xs: 'py-1 px-2 text-xs sm:text-xs',
            sm: 'py-1 px-3 text-sm sm:text-sm',
            md: 'py-1.5 px-4 text-base sm:text-base',
            lg: 'py-2 px-6 text-lg sm:text-lg',
            xlg: 'py-3 px-8 text-lg sm:text-xl',
            xxlg: 'py-4 px-12 text-xl sm:text-2xl',
        },
        disabled: {
            true: 'cursor-not-allowed opacity-60',
        },
        fullWidth: {
            true: "w-full",  // Apply full width when true
            false: "w-auto",  // Default to auto width
        },
    },
    defaultVariants: {
        variant: "default",
        size: "md",
        fullWidth: false,
    },
    compoundVariants: [
        {
            variant: "curate",
            disabled: true,
            class: "bg-red-300 hover:bg-red-300 text-red-100",
        },
        {
            variant: ['default', 'outline', 'info', 'success'],
            disabled: true,
            class: "bg-gray-400 hover:bg-gray-400 text-gray-100",
        },
        {
            variant: ['edit', 'add'],
            disabled: true,
            class: "opacity-50 hover:bg-gray-100 text-gray-400 border-gray-300",
        }
    ],
});
</script>

<button
    {type}
    class={buttonVariants({ variant, size, disabled, fullWidth }) + " " + className}
    {style}
    onclick={(event) => {
      if (!disabled) {
        dispatch('click', event);
        onClick(event);
      }
    }}
    {disabled}
    aria-label={ariaLabel || undefined}
    aria-haspopup={ariaHaspopup ? "true" : undefined}
    aria-expanded={ariaExpanded ? "true" : undefined}
    aria-disabled={disabled}
    {id}
    tabindex={disabled ? -1 : tabIndex}
>
    {#if children}
      {@render children()}
    {/if}
</button>

<style>
</style>