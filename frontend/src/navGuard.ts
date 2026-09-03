let guard: (() => boolean) | null = null;

export function setNavGuard(fn: (() => boolean) | null) {
  guard = fn;
}

export function confirmNavigation(): boolean {
  if (!guard) return true;
  return guard();
}
