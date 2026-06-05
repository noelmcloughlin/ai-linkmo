<script lang="ts">
  // Tailwind requires the full class names to appear in source for the JIT
  // scanner to include them. Map prop values to static class strings rather
  // than interpolating, otherwise the styles silently drop.
  type Color = 'green' | 'blue' | 'red' | 'slate';
  type Position = 'left' | 'right';
  type Pad = '1' | '2' | '3' | '4';
  type TextSize = 'xs' | 'sm' | 'base' | 'lg' | 'xl';

  const colorClasses: Record<Color, string> = {
    green: 'bg-green-600 hover:bg-green-700 focus:ring-green-400',
    blue: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-400',
    red: 'bg-red-600 hover:bg-red-700 focus:ring-red-400',
    slate: 'bg-slate-600 hover:bg-slate-700 focus:ring-slate-400'
  };
  const positionClasses: Record<Position, string> = {
    left: 'left-2',
    right: 'right-2'
  };
  const pxClasses: Record<Pad, string> = {
    '1': 'px-1',
    '2': 'px-2',
    '3': 'px-3',
    '4': 'px-4'
  };
  const pyClasses: Record<Pad, string> = {
    '1': 'py-1',
    '2': 'py-2',
    '3': 'py-3',
    '4': 'py-4'
  };
  const textSizeClasses: Record<TextSize, string> = {
    xs: 'text-xs',
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  let {
    position = 'left' as Position,
    color = 'green' as Color,
    icon = 'X',
    ariaLabel = 'Toggle menu',
    onClick = (_event: MouseEvent & { currentTarget: HTMLButtonElement }) => {},
    style = '',
    px = '3' as Pad,
    py = '2' as Pad,
    textSize = 'lg' as TextSize
  } = $props();
</script>

<button
  class="fixed z-50 rounded-full text-white shadow-lg transition-all duration-150 focus:ring-2 focus:outline-none {positionClasses[
    position as Position
  ]} {colorClasses[color as Color]} {pxClasses[px as Pad]} {pyClasses[py as Pad]} {textSizeClasses[
    textSize as TextSize
  ]}"
  {style}
  type="button"
  aria-label={ariaLabel}
  onclick={(event) => onClick(event as MouseEvent & { currentTarget: HTMLButtonElement })}
>
  {icon}
</button>
