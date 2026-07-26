/**
 * Every React Query key in one place.
 *
 * Invalidation is only correct if the key used to write matches the key used
 * to read. Building them from shared factories means a typo is a missing
 * import rather than a silently stale screen.
 */

export const queryKeys = {
  dashboard: ["dashboard"],

  companies: {
    all: ["companies"],
    list: (params) => ["companies", "list", params],
    detail: (id) => ["companies", "detail", id],
  },

  notes: {
    all: ["notes"],
    list: (params) => ["notes", "list", params],
  },

  contacts: {
    all: ["contacts"],
    list: (params) => ["contacts", "list", params],
    detail: (id) => ["contacts", "detail", id],
  },

  applications: {
    all: ["applications"],
    list: (params) => ["applications", "list", params],
  },

  scans: {
    all: ["scans"],
    status: (id) => ["scans", "status", id],
  },
};
