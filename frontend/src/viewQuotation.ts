import { getQuotationViewHtml } from "./api/endpoints";

export async function openQuotationView(id: string) {
  const html = await getQuotationViewHtml(id);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
