import { TOKEN_KEY } from "./api/client";

export function openQuotationView(quoteNumber: string) {
  const token = localStorage.getItem(TOKEN_KEY);
  const url = `/quote/${quoteNumber.toLowerCase()}${token ? `?token=${encodeURIComponent(token)}` : ""}`;
  window.open(url, "_blank");
}
