<script lang="ts">
  interface Props {
    id: string;
    itemprop?: string;
    itemtype?: string;
    checked: boolean;
    disabled: boolean;
    label?: string;
    onchange: (checked: boolean) => void;
  }

  let {
    id,
    itemprop = 'checkbox',
    itemtype = 'http://schema.org/Thing',
    checked = $bindable(false),
    disabled,
    label = 'fetch related records',
    onchange
  }: Props = $props();
</script>

<div class="mt-0 mb-0.5 flex flex-row items-center gap-1 pl-1">
  <input
    {id}
    {itemprop}
    {itemtype}
    type="checkbox"
    bind:checked
    {disabled}
    onchange={(e) => {
      const isChecked = (e.target as HTMLInputElement).checked;
      onchange(isChecked);
    }}
    class="checkbox checkbox-info mr-1 {disabled && !checked ? 'cursor-not-allowed' : ''}"
    style="transform: scale(1.2); margin-right: 0.25rem;"
  />
  <label
    for={id}
    class="label label-text mb-0 cursor-pointer text-sm leading-tight text-black"
    style="font-size:0.875rem; padding-top: 0; padding-bottom: 0;"
  >
    {label}
  </label>
</div>
