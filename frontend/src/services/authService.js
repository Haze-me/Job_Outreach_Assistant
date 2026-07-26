/**
 * Authentication API calls.
 *
 * Services are thin wrappers that return unwrapped data, so components and
 * hooks never touch Axios response objects.
 */

import apiClient from "./apiClient";

export async function register({ email, password, passwordConfirm, firstName, lastName }) {
  const { data } = await apiClient.post("/auth/register/", {
    email,
    password,
    password_confirm: passwordConfirm,
    first_name: firstName ?? "",
    last_name: lastName ?? "",
  });
  return data; // { access, refresh, user }
}

export async function login({ email, password }) {
  const { data } = await apiClient.post("/auth/login/", { email, password });
  return data; // { access, refresh, user }
}

/**
 * Ends the session server-side by blacklisting the refresh token.
 *
 * The access token stays valid until it expires (15 minutes); blacklisting the
 * refresh token is what stops the session being renewed.
 */
export async function logout({ refresh }) {
  const { data } = await apiClient.post("/auth/logout/", { refresh });
  return data;
}

export async function fetchProfile() {
  const { data } = await apiClient.get("/auth/profile/");
  return data;
}

export async function updateProfile({ firstName, lastName }) {
  const { data } = await apiClient.patch("/auth/profile/", {
    first_name: firstName,
    last_name: lastName,
  });
  return data;
}

/**
 * Changes the password and returns a fresh token pair.
 *
 * The backend revokes every other session, so the new pair must be stored or
 * the current device signs itself out.
 */
export async function changePassword({ currentPassword, newPassword, newPasswordConfirm }) {
  const { data } = await apiClient.post("/auth/change-password/", {
    current_password: currentPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  });
  return data; // { access, refresh, detail }
}
