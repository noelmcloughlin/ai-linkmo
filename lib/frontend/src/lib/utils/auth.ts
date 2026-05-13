// lib/frontend/src/lib/utils/auth.ts

import { authState } from "$states/index";
import { DEFAULT_PERSONAS } from "$lib/constants";
export const personas = DEFAULT_PERSONAS;

export function selectPersona(
  persona: { name: string; avatar: string } | null,
): void {
  authState.user = persona ?? personas[0];
}

export function login(
  persona: { name: string; avatar: string } | null = null,
): void {
  authState.loggedIn = true;
  selectPersona(persona);
}

export function logout(): void {
  authState.loggedIn = false;
  authState.user = null;
}