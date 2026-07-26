/**
 * Joins class names, dropping falsy values.
 *
 * Deliberately tiny: it keeps conditional classes readable
 * (`cn("base", isActive && "active")`) without pulling in a dependency.
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}
