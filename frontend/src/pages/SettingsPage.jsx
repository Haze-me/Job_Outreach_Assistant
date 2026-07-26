import { useState } from "react";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card, CardHeader } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageHeader } from "../components/ui/PageHeader";
import { useAuth } from "../hooks/useAuth";
import * as authService from "../services/authService";
import { setTokens } from "../store/tokenStorage";
import { formatDateTime } from "../utils/format";
import { getErrorMessage, getFieldErrors } from "../utils/errors";

const EMPTY_PASSWORD_FORM = {
  currentPassword: "",
  newPassword: "",
  newPasswordConfirm: "",
};

/**
 * Account settings.
 *
 * The specification lists Profile and Settings as separate pages without
 * saying what belongs on each. The split used here: Profile holds who you are
 * (name, email), Settings holds account security. The password form lives
 * here rather than being duplicated.
 */
export function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" description="Account security and session information." />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChangePasswordCard />
        <AccountCard />
      </div>
    </>
  );
}

function ChangePasswordCard() {
  const [form, setForm] = useState(EMPTY_PASSWORD_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [status, setStatus] = useState(null);
  const [isSaving, setSaving] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setStatus(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    setFieldErrors({});

    try {
      const { access, refresh } = await authService.changePassword(form);
      // The API revokes every session and issues a fresh pair for this device.
      // Storing it is what keeps the current tab signed in.
      setTokens({ access, refresh });
      setForm(EMPTY_PASSWORD_FORM);
      setStatus({
        variant: "success",
        message: "Password changed. Any other devices have been signed out.",
      });
    } catch (error) {
      setStatus({ variant: "error", message: getErrorMessage(error) });
      setFieldErrors(getFieldErrors(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Password" description="Changing it signs out every other device." />

      {status && (
        <Alert variant={status.variant} className="mb-5">
          {status.message}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Current password"
          name="currentPassword"
          type="password"
          autoComplete="current-password"
          value={form.currentPassword}
          onChange={handleChange}
          error={fieldErrors.current_password}
          required
        />
        <Input
          label="New password"
          name="newPassword"
          type="password"
          autoComplete="new-password"
          value={form.newPassword}
          onChange={handleChange}
          error={fieldErrors.new_password}
          hint="At least 8 characters, and different from your current one."
          required
        />
        <Input
          label="Confirm new password"
          name="newPasswordConfirm"
          type="password"
          autoComplete="new-password"
          value={form.newPasswordConfirm}
          onChange={handleChange}
          error={fieldErrors.new_password_confirm}
          required
        />

        <Button type="submit" isLoading={isSaving}>
          Change password
        </Button>
      </form>
    </Card>
  );
}

function AccountCard() {
  const { user, logout } = useAuth();
  const [isSigningOut, setSigningOut] = useState(false);

  return (
    <Card className="h-fit">
      <CardHeader title="Account" />

      <dl className="space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Email</dt>
          <dd className="font-medium text-slate-900">{user?.email}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Name</dt>
          <dd className="font-medium text-slate-900">{user?.full_name || "—"}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Joined</dt>
          <dd className="font-medium text-slate-900">{formatDateTime(user?.date_joined)}</dd>
        </div>
      </dl>

      <div className="mt-6 border-t border-slate-100 pt-5">
        <p className="mb-3 text-sm text-slate-500">
          Signing out ends this session on this device.
        </p>
        <Button
          variant="secondary"
          isLoading={isSigningOut}
          onClick={async () => {
            setSigningOut(true);
            try {
              await logout();
            } finally {
              setSigningOut(false);
            }
          }}
        >
          Sign out
        </Button>
      </div>
    </Card>
  );
}
