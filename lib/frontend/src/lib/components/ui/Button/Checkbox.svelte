<script lang="ts">
    interface Props {
        id: string;
        checked?: boolean;
        disabled?: boolean;
        label?: string;
        labelClass?: string;
        checkboxClass?: string;
        containerClass?: string;
        scale?: number;
        onchange?: (checked: boolean) => void;
    }

    let {
        id,
        checked = $bindable(false),
        disabled = false,
        label,
        labelClass = 'label label-text text-white mb-0.5 cursor-pointer',
        checkboxClass = 'checkbox checkbox-info checkbox-scaled',
        containerClass = 'flex flex-row items-center gap-2',
        scale = 1.0,
        onchange
    }: Props = $props();
</script>

<div class={containerClass}>
    <input
        {id}
        type="checkbox"
        bind:checked
        {disabled}
        onchange={(e) => {
            const isChecked = (e.target as HTMLInputElement).checked;
            if (onchange) {
                onchange(isChecked);
            }
        }}
        class={checkboxClass}
        style="transform: scale({scale});"
    />
    {#if label}
        <label
         for={id}
         class={labelClass}
        >
            {label}
        </label>
    {/if}
</div>