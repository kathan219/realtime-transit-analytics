/**
 * TTC Route Information
 */
export const TTC_ROUTES = {
  "504": {
    name: "King",
    description: "King St West ↔ Downtown",
    directions: ["inbound", "outbound"]
  },
  "501": {
    name: "Queen",
    description: "Queen St East ↔ West",
    directions: ["inbound", "outbound"]
  },
  "505": {
    name: "Dundas",
    description: "Dundas St West ↔ Downtown",
    directions: ["inbound", "outbound"]
  },
  "506": {
    name: "Carlton",
    description: "Carlton St ↔ Downtown",
    directions: ["inbound", "outbound"]
  },
  "509": {
    name: "Harbourfront",
    description: "Harbourfront ↔ Union Station",
    directions: ["inbound", "outbound"]
  },
  "510": {
    name: "Spadina",
    description: "Spadina Ave ↔ Union Station",
    directions: ["inbound", "outbound"]
  },
  "511": {
    name: "Bathurst",
    description: "Bathurst St ↔ Downtown",
    directions: ["inbound", "outbound"]
  },
  "512": {
    name: "St. Clair",
    description: "St. Clair Ave ↔ Downtown",
    directions: ["inbound", "outbound"]
  },
};

export const ROUTE_IDS = Object.keys(TTC_ROUTES);

export const DIRECTIONS = [
  { label: "Both Directions", value: "both" },
  { label: "Inbound (→ Downtown)", value: "inbound" },
  { label: "Outbound (← Suburbs)", value: "outbound" },
];

