import { NavLink } from "react-router-dom";

import { cn } from "../../utils/cn";

/** Primary navigation, matching the specification's authenticated page list. */
const NAV_GROUPS = [
  {
    label: "Outreach",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: DashboardIcon },
      { to: "/companies", label: "Companies", icon: BuildingIcon },
      { to: "/contacts", label: "Contacts", icon: MailIcon },
      { to: "/applications", label: "Applications", icon: BriefcaseIcon },
      { to: "/notes", label: "Notes", icon: NoteIcon },
    ],
  },
  {
    label: "Account",
    items: [
      { to: "/profile", label: "Profile", icon: ProfileIcon },
      { to: "/settings", label: "Settings", icon: SettingsIcon },
    ],
  },
];

export function Sidebar({ onNavigate }) {
  return (
    <nav aria-label="Main" className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <div className="px-2 pt-1">
        <p className="text-sm font-semibold text-slate-900">Job Outreach</p>
        <p className="text-xs text-slate-500">Assistant</p>
      </div>

      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="flex flex-col gap-1">
          <p className="px-3 pb-1 text-xs font-semibold tracking-wide text-slate-400 uppercase">
            {group.label}
          </p>
          {group.items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onNavigate}
              // `end` on /dashboard only; the others should stay highlighted
              // on their nested routes (e.g. /companies/:id).
              end={to === "/dashboard"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn("size-5 shrink-0", isActive ? "text-brand-600" : "text-slate-400")} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}

function DashboardIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z" />
    </svg>
  );
}

function BuildingIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16M15 21V9h4a1 1 0 0 1 1 1v11M3 21h18M7 8h4M7 12h4M7 16h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function MailIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="m3.5 7 8.5 6 8.5-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function BriefcaseIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="7" width="18" height="13" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M3 12h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function NoteIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 9h8M8 13h8M8 17h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function ProfileIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0 2c-4 0-7 2-7 4.5V21h14v-2.5C19 16 16 14 12 14Z" />
    </svg>
  );
}

function SettingsIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
      <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 9 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 9a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
