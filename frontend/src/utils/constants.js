/**
 * Labels for the backend's enumerations.
 *
 * These mirror `ApplicationStatus`, `ContactClassification`, `ScanStatus` and
 * `PageType` on the server. The values must match exactly -- they are sent as
 * filter parameters and written back on update. Only the display strings live
 * here; the source of truth for what is valid is the API, which rejects
 * anything it does not recognise.
 */

export const APPLICATION_STATUSES = [
  { value: "draft", label: "Draft", tone: "neutral" },
  { value: "sent", label: "Sent", tone: "brand" },
  { value: "waiting", label: "Waiting", tone: "warning" },
  { value: "interview", label: "Interview", tone: "brand" },
  { value: "offer", label: "Offer", tone: "positive" },
  { value: "rejected", label: "Rejected", tone: "negative" },
  { value: "closed", label: "Closed", tone: "neutral" },
];

export const APPLICATION_STATUS_LABELS = Object.fromEntries(
  APPLICATION_STATUSES.map(({ value, label }) => [value, label]),
);

export const APPLICATION_STATUS_TONES = Object.fromEntries(
  APPLICATION_STATUSES.map(({ value, tone }) => [value, tone]),
);

export const CONTACT_CLASSIFICATIONS = [
  { value: "hr", label: "HR", tone: "brand" },
  { value: "recruitment", label: "Recruitment", tone: "brand" },
  { value: "careers", label: "Careers", tone: "brand" },
  { value: "talent", label: "Talent", tone: "brand" },
  { value: "jobs", label: "Jobs", tone: "brand" },
  { value: "support", label: "Support", tone: "neutral" },
  { value: "sales", label: "Sales", tone: "neutral" },
  { value: "media", label: "Media", tone: "neutral" },
  { value: "general", label: "General", tone: "neutral" },
  { value: "unknown", label: "Unknown", tone: "muted" },
];

export const CONTACT_CLASSIFICATION_LABELS = Object.fromEntries(
  CONTACT_CLASSIFICATIONS.map(({ value, label }) => [value, label]),
);

export const CONTACT_CLASSIFICATION_TONES = Object.fromEntries(
  CONTACT_CLASSIFICATIONS.map(({ value, tone }) => [value, tone]),
);

/** The five categories the API groups under `recruitment_only`. */
export const RECRUITMENT_CLASSIFICATIONS = ["hr", "recruitment", "careers", "talent", "jobs"];

export const SCAN_STATUS_TONES = {
  pending: "neutral",
  running: "brand",
  completed: "positive",
  failed: "negative",
};

export const PAGE_TYPE_LABELS = {
  home: "Home",
  about: "About",
  careers: "Careers",
  jobs: "Jobs",
  contact: "Contact",
  team: "Team",
  leadership: "Leadership",
  press: "Press",
  other: "Other",
};
